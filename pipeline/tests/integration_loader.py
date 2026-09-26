"""End-to-end loader checks using isolated source and warehouse QA databases."""

import gzip
import hashlib
import io
import json
import os
import uuid

import psycopg
from minio import Minio

from loaders import suumo_batch_loader as loader

RUN_ID = uuid.uuid4().hex[:8]
SOURCE_QA = f"qa_suumo_loader_source_{RUN_ID}"
WAREHOUSE_QA = f"qa_suumo_loader_warehouse_{RUN_ID}"
BUCKET = "suumo"
PREFIX = f"data/qa_loader_integration_{uuid.uuid4().hex}_"


def admin_connection(source: bool) -> psycopg.Connection:
    """Connect to the existing server for creating and removing a QA database."""

    config = (loader.load_source_postgres_config() if source
              else loader.load_warehouse_postgres_config())
    return psycopg.connect(host=config.host, port=config.port, user=config.user,
                           password=config.password, dbname=config.dbname,
                           autocommit=True)


def minio_client() -> Minio:
    """Build the same MinIO client configuration used by the loader."""

    config = loader.load_minio_config()
    return Minio(config.endpoint, access_key=config.access_key,
                 secret_key=config.secret_key, secure=config.secure)


def put_batch(client: Minio, batch_id: int, records: list[dict]) -> tuple[str, str]:
    """Upload one uniquely named compressed test object and return path/hash."""

    payload = gzip.compress(json.dumps(records, ensure_ascii=False).encode())
    path = f"{PREFIX}{batch_id}.json.gz"
    client.put_object(BUCKET, path, io.BytesIO(payload), len(payload),
                      content_type="application/gzip")
    return f"{BUCKET}/{path}", hashlib.sha256(payload).hexdigest()


def add_batch(batch_id: int, path: str, file_hash: str, row_count: int,
              status: str = "pending") -> None:
    """Insert source metadata in the isolated source database."""

    with loader.postgres_connection(loader.load_source_postgres_config()) as source:
        source.execute("""INSERT INTO load_batches
            (batch_id,source_id,file_path,file_format,compression,row_count,file_hash,status,started_loading_at)
            VALUES (%s,1,%s,'json','gzip',%s,%s,%s,
                    CASE WHEN %s='loading' THEN now()-interval '2 hours' END)""",
            (batch_id, path, row_count, file_hash, status, status))


def check_batch(batch_id: int, status: str, inserted: int = 0,
                failed: int = 0) -> None:
    """Assert status and counters persisted to the source database."""

    with loader.postgres_connection(loader.load_source_postgres_config()) as source:
        row = source.execute("""SELECT status,inserted_count,failed_count
            FROM load_batches WHERE batch_id=%s""", (batch_id,)).fetchone()
    assert row == (status, inserted, failed), (batch_id, row)


def raw_count() -> int:
    """Count committed warehouse rows in the isolated QA database."""

    with loader.postgres_connection(loader.load_warehouse_postgres_config()) as warehouse:
        return warehouse.execute("SELECT count(*) FROM raw.suumo_parser_records").fetchone()[0]


def run_checks(client: Minio, paths: list[str]) -> None:
    """Exercise success, integrity failures, write rollback, and manual recovery."""

    valid = {"task_id": 101, "is_valid": True, "data_hash": "a" * 64}
    invalid = {"task_id": 102, "is_valid": False, "error_type": "parse_error"}

    path, file_hash = put_batch(client, 1, [valid, invalid])
    paths.append(path.split("/", 1)[1])
    add_batch(1, path, file_hash, 2)
    assert loader.load_one_batch(1)["status"] == "success"
    check_batch(1, "success", 1, 1)
    assert raw_count() == 1

    path, file_hash = put_batch(client, 2, [valid])
    paths.append(path.split("/", 1)[1])
    add_batch(2, path, "0" * 64, 1)
    assert loader.load_one_batch(2)["status"] == "failed"
    check_batch(2, "failed")

    path, file_hash = put_batch(client, 3, [valid])
    paths.append(path.split("/", 1)[1])
    add_batch(3, path, file_hash, 2)
    assert loader.load_one_batch(3)["status"] == "failed"
    check_batch(3, "failed")

    path, file_hash = put_batch(client, 4, [{"is_valid": True}])
    paths.append(path.split("/", 1)[1])
    add_batch(4, path, file_hash, 1)
    assert loader.load_one_batch(4)["status"] == "failed"
    check_batch(4, "failed")

    first = {"task_id": 901, "is_valid": True, "data_hash": "b" * 64}
    rejected = {"task_id": 2001, "is_valid": True, "data_hash": "c" * 64}
    path, file_hash = put_batch(client, 5, [first, rejected])
    paths.append(path.split("/", 1)[1])
    add_batch(5, path, file_hash, 2)
    assert loader.load_one_batch(5)["status"] == "failed"
    check_batch(5, "failed")
    assert raw_count() == 1, "The first write in a failed batch must roll back"

    with loader.postgres_connection(loader.load_warehouse_postgres_config()) as warehouse:
        warehouse.execute("ALTER TABLE raw.suumo_parser_records DROP CONSTRAINT qa_task_limit")
    loader.reset_source_batch(5)
    check_batch(5, "pending")
    assert loader.load_one_batch(5)["status"] == "success"
    check_batch(5, "success", 2, 0)
    assert raw_count() == 3

    path, file_hash = put_batch(client, 6, [valid])
    paths.append(path.split("/", 1)[1])
    add_batch(6, path, file_hash, 1)
    assert loader.load_one_batch(6)["status"] == "success"
    check_batch(6, "success", 1, 0)
    assert raw_count() == 3, "Repeated task_id must upsert"

    path, file_hash = put_batch(client, 7, [valid])
    paths.append(path.split("/", 1)[1])
    add_batch(7, path, file_hash, 1, "loading")
    loader.reset_source_batch(7, stale_minutes=60)
    check_batch(7, "pending")
    try:
        loader.reset_source_batch(6)
    except ValueError:
        pass
    else:
        raise AssertionError("A successful batch was reset")


def main() -> None:
    """Create isolated databases, run checks, and always clean up QA state."""

    source_admin = admin_connection(True)
    warehouse_admin = admin_connection(False)
    paths = []
    try:
        source_admin.execute(f"CREATE DATABASE {SOURCE_QA}")
        warehouse_admin.execute(f"CREATE DATABASE {WAREHOUSE_QA}")
        os.environ["SOURCE_POSTGRES_DB"] = SOURCE_QA
        os.environ["WAREHOUSE_DB"] = WAREHOUSE_QA
        with loader.postgres_connection(loader.load_source_postgres_config()) as source:
            source.execute("""CREATE TABLE load_batches (
                batch_id bigint primary key, source_id bigint, file_path text,
                file_format text, compression text, row_count integer, file_hash text,
                status text, inserted_count integer default 0, failed_count integer default 0,
                started_loading_at timestamptz, finished_loading_at timestamptz,
                loaded_at timestamptz, error_message text)""")
        with loader.postgres_connection(loader.load_warehouse_postgres_config()) as warehouse:
            warehouse.execute("CREATE SCHEMA raw")
            warehouse.execute("""CREATE TABLE raw.suumo_parser_records (
                task_id bigint primary key, batch_id bigint, source_id bigint,
                data_hash text, record jsonb, loaded_at timestamptz,
                created_at timestamptz, updated_at timestamptz,
                CONSTRAINT qa_task_limit CHECK (task_id < 1000))""")
        run_checks(minio_client(), paths)
        print("Loader integration checks passed")
    finally:
        try:
            client = minio_client()
            for path in paths:
                client.remove_object(BUCKET, path)
        finally:
            source_admin.execute(f"DROP DATABASE IF EXISTS {SOURCE_QA} WITH (FORCE)")
            warehouse_admin.execute(f"DROP DATABASE IF EXISTS {WAREHOUSE_QA} WITH (FORCE)")
            source_admin.close()
            warehouse_admin.close()


if __name__ == "__main__":
    main()
