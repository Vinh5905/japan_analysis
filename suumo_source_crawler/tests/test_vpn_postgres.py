"""Opt-in transactions against a disposable local PostgreSQL database."""

import json
import os
from pathlib import Path
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "suumo_source_crawler"))
from scripts.vpn_pool import register, start_attempt, finish_attempt
import test_ward_postgres as ward_qa


@unittest.skipUnless(
    os.environ.get("SUUMO_VPN_DB_TESTS") == "1", "Opt-in local VPN DB acceptance"
)
class VpnPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Reuse the isolated QA DB harness without altering the real local DB."""
        ward_qa.WardPostgresTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        """Drop only the database created by this class."""
        ward_qa.WardPostgresTests.tearDownClass.__func__(cls)

    @classmethod
    def sql(cls, sql):
        """Execute QA SQL with errors propagated from psql."""
        return ward_qa.WardPostgresTests.sql.__func__(cls, sql)

    def setUp(self):
        """Start with a fresh schema and one running crawl, without a real VPN."""
        self.sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        fresh = (
            ROOT / "docker/postgres/init/001_create_crawler_metadata.sql"
        ).read_text()
        self.sql(fresh)
        self.rows = [
            {"filename": n, "relative_path": n, "sha256": "a" * 64}
            for n in ("a.ovpn", "b.ovpn", "c.ovpn")
        ]
        register(self.host, self.rows)
        self.run = self.host.query(
            "INSERT INTO crawl_runs(pipeline_key,pipeline_status,total_urls,created_by) VALUES('qa','running',7,'manual') RETURNING json_build_object('run_id',run_id)"
        )
        self.vpns = self.host.query(
            "SELECT json_agg(v ORDER BY filename) FROM crawl_vpns v"
        )

    def test_migration_idempotent_no_historical_guessing(self):
        migration = (
            ROOT / "docker/postgres/migrations/009_crawl_vpn_pool.sql"
        ).read_text()
        self.sql(migration)
        self.sql(migration)
        self.assertEqual(self.host.total(), {"total_urls": 7, "runs": 1})
        self.assertIsNone(self.host.history()[0]["vpn_snapshot"])
        self.assertEqual(register(self.host, self.rows), 0)
        self.assertTrue(
            all(
                v["total_requests"] == 0 and v["last_attempt_at"] is None
                for v in self.vpns
            )
        )

    def test_activation_trial_counters_order_and_finish_replay(self):
        a = start_attempt(self.host, self.run, self.vpns[0])
        finish_attempt(self.host, a, False)
        self.assertIsNone(finish_attempt(self.host, a, False))
        self.assertIsNone(start_attempt(self.host, self.run, self.vpns[0]))
        b = start_attempt(self.host, self.run, self.vpns[1])
        finish_attempt(self.host, b, True)
        self.assertEqual(register(self.host, self.rows), 0)
        rows = self.host.query(
            "SELECT json_agg(v ORDER BY last_attempt_at NULLS FIRST,filename) FROM crawl_vpns v"
        )
        self.assertEqual([v["filename"] for v in rows], ["c.ovpn", "a.ovpn", "b.ovpn"])
        self.assertEqual(
            (rows[1]["activation_failures"], rows[1]["activation_successes"]), (1, 0)
        )
        self.assertEqual(
            (rows[2]["activation_failures"], rows[2]["activation_successes"]), (0, 1)
        )
        self.assertIsNone(rows[1]["last_used_at"])
        self.assertIsNotNone(rows[2]["last_used_at"])
        self.assertEqual(self.host.history()[0]["vpn_snapshot"]["filename"], "b.ovpn")
        self.assertEqual(self.host.total()["runs"], 1)

    def test_request_idempotency_and_mismatched_context_rejected(self):
        attempt = start_attempt(self.host, self.run, self.vpns[0])
        finish_attempt(self.host, attempt, True)
        rid, vid = self.run["run_id"], self.vpns[0]["vpn_id"]
        event = str(uuid.uuid4())
        sql = f"SELECT json_build_object('added',record_crawl_vpn_request('{event}',{rid},{vid},'suumo_links'))"
        self.assertEqual(self.host.query(sql), {"added": True})
        self.assertEqual(self.host.query(sql), {"added": False})
        with self.assertRaises(RuntimeError):
            self.host.query(sql.replace("suumo_links", "suumo_html"))
        with self.assertRaises(RuntimeError):
            self.host.query(sql.replace(f",{vid},", f",{self.vpns[1]['vpn_id']},"))
        self.assertEqual(
            json.loads(
                self.sql(f"SELECT total_requests FROM crawl_vpns WHERE vpn_id={vid}")
            ),
            1,
        )
        self.sql(
            f"UPDATE crawl_runs SET pipeline_status='completed' WHERE run_id={rid}"
        )
        with self.assertRaises(RuntimeError):
            self.host.query(sql.replace(event, str(uuid.uuid4())))

    def test_failed_counter_write_rolls_back_request_journal(self):
        attempt = start_attempt(self.host, self.run, self.vpns[0])
        finish_attempt(self.host, attempt, True)
        self.sql(
            "CREATE FUNCTION reject_count() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'qa'; END $$; CREATE TRIGGER reject_count BEFORE UPDATE ON crawl_vpns FOR EACH ROW EXECUTE FUNCTION reject_count();"
        )
        with self.assertRaises(RuntimeError):
            self.host.query(
                f"SELECT json_build_object('added',record_crawl_vpn_request('{uuid.uuid4()}',{self.run['run_id']},{self.vpns[0]['vpn_id']},'suumo_html'))"
            )
        self.assertEqual(self.sql("SELECT count(*) FROM crawl_vpn_requests"), "0")
        self.assertEqual(self.sql("SELECT sum(total_requests) FROM crawl_vpns"), "0")


if __name__ == "__main__":
    unittest.main()
