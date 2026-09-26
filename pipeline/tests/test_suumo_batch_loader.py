"""Regression tests for batch integrity and atomic warehouse writes."""

import gzip
import hashlib
import json
import unittest
from unittest.mock import MagicMock, patch

from loaders import suumo_batch_loader as loader


class LoaderTests(unittest.TestCase):
    """Exercise validation before writes and batch-level failure behavior."""

    def setUp(self) -> None:
        """Build one valid batch and an in-memory MinIO response."""

        self.records = [
            {"task_id": 1, "is_valid": True, "data_hash": "a" * 64},
            {"task_id": 2, "is_valid": False, "error_type": "parse_error"},
        ]
        self.payload = gzip.compress(json.dumps(self.records).encode())
        self.batch = loader.SourceBatch(1, 1, "suumo/data/test.json.gz", "json", "gzip", 2,
                                        hashlib.sha256(self.payload).hexdigest())

    @patch.object(loader, "Minio")
    def test_read_checks_hash_and_row_count(self, minio_class) -> None:
        """Reject corrupted bytes and a metadata count mismatch."""

        minio_class.return_value.get_object.return_value.read.return_value = self.payload
        self.assertEqual(loader.read_minio_batch(self.batch), self.records)
        wrong_hash = loader.SourceBatch(1, 1, self.batch.file_path, "json", "gzip", 2, "0" * 64)
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            loader.read_minio_batch(wrong_hash)
        wrong_count = loader.SourceBatch(1, 1, self.batch.file_path, "json", "gzip", 3,
                                         self.batch.file_hash)
        with self.assertRaisesRegex(ValueError, "row_count mismatch"):
            loader.read_minio_batch(wrong_count)

    def test_validation_rejects_structure_and_duplicate_task_id(self) -> None:
        """Reject malformed records before opening a warehouse transaction."""

        for records in ([{"is_valid": True}], ["bad"], [self.records[0], self.records[0]]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                loader.validate_batch_records(records)
        valid, failed = loader.validate_batch_records(self.records)
        self.assertEqual(len(valid), 1)
        self.assertEqual(failed, 1)

    @patch.object(loader, "postgres_connection")
    @patch.object(loader, "load_warehouse_postgres_config")
    def test_write_is_one_transaction_and_repeatable(self, _, connect) -> None:
        """Use one transaction, upsert by task ID, and propagate a write error."""

        connection = connect.return_value.__enter__.return_value
        cursor = connection.cursor.return_value.__enter__.return_value
        self.assertEqual(loader.load_records_to_warehouse(self.batch, self.records),
                         {"inserted_count": 1, "failed_count": 1})
        self.assertEqual(loader.load_records_to_warehouse(self.batch, self.records),
                         {"inserted_count": 1, "failed_count": 1})
        self.assertIn("ON CONFLICT (task_id)", cursor.execute.call_args.args[0])
        self.assertEqual(connection.transaction.call_count, 2)
        cursor.execute.side_effect = RuntimeError("warehouse unavailable")
        with self.assertRaisesRegex(RuntimeError, "warehouse unavailable"):
            loader.load_records_to_warehouse(self.batch, self.records)

    @patch.object(loader, "mark_source_batch_failed")
    @patch.object(loader, "load_records_to_warehouse", side_effect=RuntimeError("write failed"))
    @patch.object(loader, "read_minio_batch")
    @patch.object(loader, "claim_source_batch")
    def test_write_error_fails_source_batch(self, claim, read, _, failed) -> None:
        """Record a warehouse write error as a failed source batch."""

        claim.return_value = self.batch
        read.return_value = self.records
        self.assertEqual(loader.load_one_batch(1)["status"], "failed")
        failed.assert_called_once_with(1, "write failed")

    @patch.object(loader, "postgres_connection")
    @patch.object(loader, "load_source_postgres_config")
    def test_recovery_checks_batch_state(self, _, connect) -> None:
        """Reset only eligible source rows, leaving success and fresh loading untouched."""

        cursor = connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (7,)
        loader.reset_source_batch(7, 90)
        query, params = cursor.execute.call_args.args
        self.assertIn("status = 'failed'", query)
        self.assertIn("status = 'loading'", query)
        self.assertEqual(params, (7, 90))
        cursor.fetchone.return_value = None
        with self.assertRaisesRegex(ValueError, "not failed or loading"):
            loader.reset_source_batch(7, 90)


if __name__ == "__main__":
    unittest.main()
