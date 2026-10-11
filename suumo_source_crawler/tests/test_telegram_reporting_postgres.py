"""Opt-in SQL acceptance checks using local Compose Postgres and TEMP fixtures.

SUUMO_TELEGRAM_DB_TESTS=1 python3 -m unittest discover -s suumo_source_crawler/tests -p test_telegram_reporting_postgres.py -v
Existing persistent tables are shadowed by transaction-local temporary tables.
"""

import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "suumo_source_crawler"))
from scripts.telegram_control import Host, host_command
from scripts.run_release_pipeline import read_env_file


FIXTURES = """
BEGIN;
CREATE TEMP TABLE crawl_runs (
 run_id bigint, source_id bigint, created_at timestamptz,
 finished_at timestamptz, created_by text, total_urls integer
);
ALTER TABLE crawl_runs ADD COLUMN area_snapshot jsonb;
ALTER TABLE crawl_runs ADD COLUMN pipeline_status text;
ALTER TABLE crawl_runs ADD COLUMN pipeline_finished_at timestamptz;
ALTER TABLE crawl_runs ADD COLUMN vpn_snapshot jsonb;
CREATE TEMP TABLE crawl_tasks (run_id bigint, raw_snapshot_id bigint, status text);
INSERT INTO crawl_runs(run_id,source_id,created_at,finished_at,created_by,total_urls) VALUES
 (1,7,'2026-10-01 00:00Z','2026-10-01 01:00Z','schedule',10),
 (2,7,'2026-10-02 00:00Z','2026-10-02 01:00Z','manual',10),
 (3,7,'2026-10-03 00:00Z','2026-10-03 01:00Z','schedule',2),
 (4,7,'2026-10-04 00:00Z','2026-10-04 01:00Z','manual',0),
 (5,7,'2026-10-05 00:00Z','2026-10-05 01:00Z','schedule',4),
 (6,7,'2026-10-05 00:00Z',NULL,'manual',1),
 (7,8,'2026-10-06 00:00Z',NULL,'schedule',999);
INSERT INTO crawl_tasks VALUES (3,1,'failed'), (3,NULL,'failed'),
 (6,NULL,'failed'), (6,NULL,'pending');
"""


@unittest.skipUnless(
    os.environ.get("SUUMO_TELEGRAM_DB_TESTS") == "1",
    "Opt-in: requires running local Compose Postgres",
)
class PostgresReportingTests(unittest.TestCase):
    def host(self, source_id=7):
        values = read_env_file(ROOT / ".env")
        values["SUUMO_SOURCE_ID"] = str(source_id)

        def command(args):
            args = list(args)
            args[-1] = FIXTURES + args[-1] + "; ROLLBACK;"
            return host_command(args)

        return Host(ROOT / ".env", ROOT / "docker-compose.yml", values, command)

    def test_history_latest_five_source_tie_and_html_snapshot_semantics(self):
        rows = self.host().history()
        self.assertEqual([row["run_id"] for row in rows], [6, 5, 4, 3, 2])
        self.assertIsNone(rows[0]["finished_at"])
        self.assertEqual((rows[0]["total_urls"], rows[0]["html_failed"]), (1, 1))
        # Parse failed after a successful download still counts as HTML success.
        self.assertEqual((rows[3]["html_success"], rows[3]["html_failed"]), (1, 1))

    def test_total_includes_old_manual_rerun_failed_and_running_excludes_other_source(
        self,
    ):
        self.assertEqual(self.host().total(), {"total_urls": 27, "runs": 6})
        self.assertEqual(self.host(9).total(), {"total_urls": 0, "runs": 0})
        self.assertEqual(self.host(9).history(), [])
