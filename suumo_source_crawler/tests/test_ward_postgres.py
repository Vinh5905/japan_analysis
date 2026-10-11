"""Opt-in acceptance on an isolated, automatically removed local QA database.
SUUMO_WARD_DB_TESTS=1 python3 -m unittest discover -s suumo_source_crawler/tests -p test_ward_postgres.py -v
"""

from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "suumo_source_crawler"))
from scripts.run_release_pipeline import read_env_file
from scripts.telegram_control import Host
from scripts.area_catalog import refresh, NAMES
from scripts.crawl_dispatcher import ZONE


@unittest.skipUnless(
    os.environ.get("SUUMO_WARD_DB_TESTS") == "1", "Opt-in local Postgres acceptance"
)
class WardPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.values = read_env_file(ROOT / ".env")
        cls.database = "ward_qa_" + uuid.uuid4().hex[:12]
        cls.container = "japan_analysis_infra_postgres"
        cls.user = cls.values["POSTGRES_USER"]
        subprocess.run(
            ["docker", "exec", cls.container, "createdb", "-U", cls.user, cls.database],
            check=True,
            capture_output=True,
        )
        cls.values["POSTGRES_DB"] = cls.database

        def command(args):
            return cls.sql(args[-1])

        cls.host = Host(ROOT / ".env", ROOT / "docker-compose.yml", cls.values, command)

    @classmethod
    def tearDownClass(cls):
        subprocess.run(
            ["docker", "exec", cls.container, "dropdb", "-U", cls.user, cls.database],
            check=True,
            capture_output=True,
        )

    @classmethod
    def sql(cls, sql):
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                cls.container,
                "psql",
                "-X",
                "-q",
                "-A",
                "-t",
                "-v",
                "ON_ERROR_STOP=1",
                "-U",
                cls.user,
                "-d",
                cls.database,
            ],
            input=sql,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr)
        return result.stdout.strip()

    def setUp(self):
        fresh = (
            ROOT / "docker/postgres/init/001_create_crawler_metadata.sql"
        ).read_text()
        # Upgrade from the actual old structure, retaining seeded source/config.
        old = (
            fresh.split("CREATE TABLE IF NOT EXISTS crawl_area_catalogs")[0] + "COMMIT;"
        )
        self.sql(old)
        self.sql(
            "INSERT INTO crawl_runs(source_id,total_urls,created_by) VALUES(1,10,'manual'),(1,20,'schedule');"
        )
        self.migration = (
            ROOT / "docker/postgres/migrations/008_crawl_areas_and_pipeline.sql"
        ).read_text()
        self.sql(self.migration)
        self.sql(
            (ROOT / "docker/postgres/migrations/009_crawl_vpn_pool.sql").read_text()
        )

    def html(self, codes=None):
        rows = self.host.areas()
        return "".join(
            f'<input type="checkbox" name="sc" value="{(codes or {}).get(a["ward"], a["sc"])}" id="a{a["area_id"]}"><label for="a{a["area_id"]}">大阪市{a["ward"]}(123)</label>'
            for a in rows
        )

    def test_migration_backfills_yodogawa_keeps_totals_and_unknown_pipeline(self):
        areas = self.host.areas()
        self.assertEqual(len(areas), 24)
        y = next(a for a in areas if a["ward"] == "淀川区")
        self.assertEqual(y["runs"], 2)
        self.assertEqual(self.host.total(), {"total_urls": 30, "runs": 2})
        self.assertTrue(all(r["pipeline_status"] is None for r in self.host.history()))
        self.sql(self.migration)
        self.assertEqual(self.host.areas(), areas)

    def test_first_sync_then_skip_without_fetching(self):
        self.assertEqual(
            refresh(self.host, html=self.html()),
            {"added": 0, "updated": 0, "unchanged": 24},
        )
        self.assertEqual(refresh(self.host), {"skipped": True})

    def test_refresh_swapped_sc_preserves_ids_names_and_history(self):
        before = self.host.areas()
        a, b = before[:2]
        refresh(self.host, html=self.html())
        result = refresh(
            self.host, True, html=self.html({a["ward"]: b["sc"], b["ward"]: a["sc"]})
        )
        self.assertEqual(result, {"added": 0, "updated": 2, "unchanged": 22})
        after = {a["area_id"]: a for a in self.host.areas()}
        for row in before:
            for key in (
                "area_id",
                "prefecture",
                "ward",
                "display_name",
                "runs",
                "last_run",
            ):
                self.assertEqual(after[row["area_id"]][key], row[key])

    def test_invalid_html_and_database_error_leave_catalog_unchanged(self):
        refresh(self.host, html=self.html())
        before = self.host.areas()
        with self.assertRaises(ValueError):
            refresh(self.host, True, html=self.html() + self.html())
        # Trigger fails late, after area upserts, proving timestamp and all rows roll back.
        self.sql(
            "CREATE FUNCTION reject_catalog() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'qa'; END $$; CREATE TRIGGER reject_sync BEFORE UPDATE ON crawl_area_catalogs FOR EACH ROW EXECUTE FUNCTION reject_catalog();"
        )
        with self.assertRaises(RuntimeError):
            refresh(self.host, True, html=self.html({"淀川区": "29999"}))
        self.assertEqual(self.host.areas(), before)
        self.sql("DROP FUNCTION reject_catalog() CASCADE;")

    def test_new_ward_added_preserves_old_rows(self):
        html = (
            self.html()
            + '<input type="checkbox" name="sc" value="29999" id="new"><label for="new">大阪市試験区(1)</label>'
        )
        self.assertEqual(
            refresh(self.host, True, html=html),
            {"added": 1, "updated": 0, "unchanged": 24},
        )
        self.assertEqual(len(self.host.areas()), 25)

    def test_daily_start_time_midnight_and_preflight_failure_counts(self):
        a = self.host.areas()[0]["area_id"]
        self.sql("TRUNCATE crawl_runs CASCADE;")
        self.sql(f"""INSERT INTO crawl_runs(source_id,area_id,total_urls,created_at,pipeline_status,created_by)
          VALUES(1,{a},100,'2026-10-09 16:59:00Z','completed','schedule'),
          (1,{a},0,'2026-10-09 17:00:00Z','preflight_failed','manual'),
          (1,{a},50,'2026-10-09 17:01:00Z','crawl_failed','schedule');
          UPDATE crawl_runs SET pipeline_finished_at='2026-10-09 18:00Z';""")
        yesterday = datetime(2026, 10, 9, 23, 59, tzinfo=ZONE).timestamp()
        today = datetime(2026, 10, 10, 1, tzinfo=ZONE).timestamp()
        self.assertEqual(self.host.daily(yesterday), {"runs": 1, "total_urls": 100})
        self.assertEqual(self.host.daily(today), {"runs": 2, "total_urls": 50})
        self.assertEqual(self.host.areas(today)[0]["today_runs"], 2)

    def test_fresh_init_and_pipeline_key_unique(self):
        self.sql(
            (ROOT / "docker/postgres/init/001_create_crawler_metadata.sql").read_text()
        )
        a = self.host.areas()[0]["area_id"]
        for _ in range(2):
            self.sql(
                f"INSERT INTO crawl_runs(area_id,pipeline_key) VALUES({a},'key') ON CONFLICT(pipeline_key) DO NOTHING;"
            )
        self.assertEqual(self.host.total()["runs"], 1)


if __name__ == "__main__":
    unittest.main()
