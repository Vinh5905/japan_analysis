"""Acceptance of ward selection, durable launches, budgets and failure recovery."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.area_catalog import parse_catalog, ward_url, NAMES, DEFAULT_SEARCH_URL
from scripts.crawl_dispatcher import (
    dispatch,
    decision,
    choose_area,
    prepare,
    persist_finish,
    ZONE,
)
from scripts.runtime_lock import release_lock
from scripts.telegram_state import ControlState


def timestamp(value):
    return datetime.fromisoformat(value).replace(tzinfo=ZONE).timestamp()


def area(identifier=1, runs=0, last=None, today=0):
    return {
        "area_id": identifier,
        "sc": str(27100 + identifier),
        "prefecture": "大阪府",
        "district": None,
        "municipality": "大阪市",
        "ward": "淀川区",
        "display_name": "Yodogawa",
        "runs": runs,
        "last_run": last,
        "today_runs": today,
    }


def catalog():
    return "".join(
        f'<input type="checkbox" name="sc" value="{27100 + i}" id="a{i}"><label for="a{i}"><span>大阪市{ward}</span><span>(123)</span></label>'
        for i, ward in enumerate(NAMES, 1)
    )


class FakeHost:
    def __init__(self, base):
        self.env_file = base / ".env"
        self.values = {
            "SUUMO_SEARCH_URL": "https://suumo.jp/chintai/?sc=27123&sc=27127&cb=0"
        }
        self.source_id = 1
        self.started = 0
        self.busy_value = False
        self.unresolved_value = None
        self.existing = None
        self.daily_value = {"runs": 0, "total_urls": 0}
        self.area_values = [area()]
        self.sql = []

    def busy(self):
        return self.busy_value

    def unresolved(self):
        return self.unresolved_value

    def vpn_stopped(self):
        return False

    def pipeline_by_key(self, key):
        return self.existing

    def daily(self, now):
        return self.daily_value

    def areas(self, now=None):
        return self.area_values

    def start(self):
        self.started += 1

    def query(self, sql):
        self.sql.append(sql)
        return {"run_id": 42, "created_at": 1000, "status": "running", "source_id": 1}


class WardDispatcherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.state = ControlState(self.base / "state.sqlite3")
        self.host = FakeHost(self.base)
        self.now = timestamp("2026-10-10T10:00:00")
        self.state.set("automatic_start_at", timestamp("2026-10-10T00:00:00"))
        patcher = patch("scripts.crawl_dispatcher.refresh")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_parse_catalog_ignores_other_cities_and_requires_all_wards(self):
        rows = parse_catalog(catalog() + '<label for="sakai">堺市堺区</label>')
        self.assertEqual(len(rows), 24)
        self.assertEqual(set(r["ward"] for r in rows), set(NAMES))
        with self.assertRaises(ValueError):
            parse_catalog(catalog().replace("大阪市淀川区", "other"))

    def test_duplicate_ward_or_sc_aborts(self):
        for html in (
            catalog() + catalog(),
            catalog().replace('value="27102"', 'value="27101"'),
        ):
            with self.assertRaises(ValueError):
                parse_catalog(html)

    def test_one_ward_preserves_configuration_removes_all_sc_and_page(self):
        from urllib.parse import parse_qs, urlsplit

        url = ward_url(
            self.host.values["SUUMO_SEARCH_URL"] + "&page=10&bs=040", "27123"
        )
        self.assertEqual(
            parse_qs(urlsplit(url).query), {"sc": ["27123"], "cb": ["0"], "bs": ["040"]}
        )
        for base in ("https://evil.example/?sc=1", "http://suumo.jp/"):
            with self.assertRaises(ValueError):
                ward_url(base, "27123")

    def test_empty_release_url_uses_the_spiders_existing_filters(self):
        """Blank/missing optional config must launch, preserving the deployed spider defaults."""
        import ast
        from urllib.parse import parse_qs, urlsplit

        settings = ast.parse((ROOT / "crawler/crawler/settings.py").read_text())
        assignment = next(
            n
            for n in settings.body
            if isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "SUUMO_SEARCH_URL"
                for t in n.targets
            )
        )
        self.assertEqual(
            DEFAULT_SEARCH_URL, ast.literal_eval(assignment.value.values[-1])
        )
        for value in ("", None):
            query = parse_qs(
                urlsplit(ward_url(value, "27102")).query, keep_blank_values=True
            )
            self.assertEqual(query["sc"], ["27102"])
            self.assertEqual(query["ar"], ["060"])
            self.assertEqual(query["bs"], ["040"])
            self.assertEqual(query["cb"], ["0.0"])
            self.assertEqual(query["fw2"], [""])

    def test_manual_queue_starts_with_blank_url_before_automatic_start(self):
        """Reproduce the live confirmed Miyakojima queue without consuming it prematurely."""
        self.host.values["SUUMO_SEARCH_URL"] = ""
        self.state.set("automatic_start_at", self.now + 3600)
        self.state.request_start(self.now, area())
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 1)
        self.assertIsNotNone(self.state.get("start_request"))
        self.assertIn("sc=27101", self.state.get("pipeline")["area"]["search_url"])
        self.assertEqual(prepare(self.host, self.state)["source"], "manual")
        self.assertIsNone(self.state.get("start_request"))

    def test_fair_selection_then_oldest_then_code(self):
        self.assertEqual(choose_area([area(1, 10), area(2, 1)])["area_id"], 2)
        self.assertEqual(
            choose_area([area(1, 1, "2026-10-10"), area(2, 1, "2026-10-09")])[
                "area_id"
            ],
            2,
        )
        self.assertEqual(choose_area([area(2), area(1)])["area_id"], 1)
        self.assertEqual(choose_area([area(1, 0, today=1), area(2, 20)])["area_id"], 2)

    def test_schedule_starts_on_explicit_next_midnight(self):
        self.state.set("automatic_start_at", self.now + 100)
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)
        dispatch(self.host, self.state, self.now + 100)
        self.assertEqual(self.host.started, 1)

    def test_missing_schedule_start_never_auto_runs(self):
        self.state.set("automatic_start_at", None)
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)

    def test_target_and_max_runs_block_auto_including_zero_url_failures(self):
        for daily in (
            {"runs": 5, "total_urls": 0},
            {"runs": 1, "total_urls": 10000},
            {"runs": 6, "total_urls": 9000},
        ):
            self.host.daily_value = daily
            dispatch(self.host, self.state, self.now)
            self.assertEqual(self.host.started, 0)

    def test_manual_runs_over_limit_and_keeps_queue_until_db_created(self):
        self.host.daily_value = {"runs": 5, "total_urls": 10000}
        self.state.request_start(self.now, area())
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 1)
        self.assertIsNotNone(self.state.get("start_request"))
        run = prepare(self.host, self.state)
        self.assertEqual(run["run_id"], "42")
        self.assertEqual(run["source"], "manual")
        self.assertIsNone(self.state.get("start_request"))
        self.assertIn("INSERT INTO crawl_runs", self.host.sql[0])
        self.assertIn("'running'", self.host.sql[0])

    def test_db_unavailable_never_starts_or_consumes_queue(self):
        self.state.request_start(self.now, area())
        with patch.object(self.host, "unresolved", side_effect=RuntimeError("DB down")):
            with self.assertRaises(RuntimeError):
                dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)
        self.assertIsNotNone(self.state.get("start_request"))

    def test_busy_container_or_cleanup_retains_queue(self):
        self.state.request_start(self.now, area())
        self.host.busy_value = True
        dispatch(self.host, self.state, self.now)
        self.host.busy_value = False
        self.host.unresolved_value = {"run_id": 42}
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)
        self.assertIsNotNone(self.state.get("start_request"))

    def test_shared_lock_blocks_dispatch_during_runner_or_deploy(self):
        with release_lock(self.base), self.assertRaises(RuntimeError):
            dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)

    def test_crash_before_systemctl_reuses_same_key_after_restart(self):
        self.state.request_start(self.now, area())
        with patch.object(self.host, "start", side_effect=OSError("crash")):
            with self.assertRaises(OSError):
                dispatch(self.host, self.state, self.now)
        key = self.state.get("pipeline")["pipeline_key"]
        dispatch(self.host, ControlState(self.state.path), self.now + 1000)
        self.assertEqual(self.state.get("pipeline")["pipeline_key"], key)
        self.assertEqual(self.host.started, 1)

    def test_reboot_recovery_requires_three_spaced_shutdown_observations(self):
        self.state.request_start(self.now, area())
        pending = self.state.get("start_request")
        self.host.unresolved_value = {
            "run_id": 42,
            "pipeline_key": pending["id"],
            "created_by": "manual",
            "area_snapshot": area(),
            "started": self.now - 3600,
        }
        with (
            patch.object(self.host, "vpn_stopped", return_value=True),
            patch.object(
                self.host, "query", return_value={"cleanup_epoch": self.now + 120}
            ),
        ):
            dispatch(self.host, self.state, self.now)
            dispatch(
                self.host, self.state, self.now + 1
            )  # Duplicate wake is not another check.
            self.assertEqual(self.state.get("recovery_observation")["checks"], 1)
            dispatch(self.host, self.state, self.now + 60)
            self.assertIsNotNone(self.state.get("start_request"))
            dispatch(self.host, self.state, self.now + 120)
        self.assertIsNone(self.state.get("start_request"))
        self.assertEqual(self.state.get("next_auto_at"), self.now + 120 + 3600)
        self.assertEqual(self.host.started, 0)
        self.assertTrue(self.state.get("pipeline")["cleanup_confirmed"])

    def test_unconfirmed_shutdown_resets_restart_observations(self):
        self.host.unresolved_value = {"run_id": 42, "pipeline_key": "key"}
        with patch.object(self.host, "vpn_stopped", return_value=True):
            dispatch(self.host, self.state, self.now)
        dispatch(self.host, self.state, self.now + 60)
        self.assertEqual(self.state.get("recovery_observation"), {})
        self.assertEqual(self.host.started, 0)

    def test_db_created_before_sqlite_begin_is_not_replayed(self):
        self.state.launch(area(), "manual")
        self.host.unresolved_value = {"run_id": 42}
        dispatch(self.host, self.state, self.now)
        self.assertEqual(self.host.started, 0)

    def test_cleanup_db_committed_before_sqlite_is_recovered(self):
        self.state.launch(area(), "manual")
        key = self.state.get("pipeline")["pipeline_key"]
        self.host.existing = {
            "cleanup_confirmed_at": "done",
            "cleanup_epoch": self.now,
            "run_id": 42,
        }
        dispatch(self.host, ControlState(self.state.path), self.now + 30)
        self.assertEqual(self.host.started, 0)
        self.assertEqual(self.state.get("next_auto_at"), self.now + 3600)
        self.assertEqual(self.state.get("pipeline")["pipeline_key"], key)

    def test_manual_completion_replaces_old_rest_time(self):
        self.state.set("next_auto_at", timestamp("2026-10-10T11:00:00"))
        self.state.launch(area(), "manual")
        self.state.begin(run_id=42, created_at=self.now)
        finished = timestamp("2026-10-10T10:50:00")
        with patch("scripts.crawl_dispatcher.time.time", return_value=finished):
            persist_finish(self.host, self.state, True, True)
        self.assertEqual(
            self.state.get("next_auto_at"), timestamp("2026-10-10T11:50:00")
        )
        reason, due = decision(self.state, {"runs": 1, "total_urls": 100}, finished)
        self.assertEqual(due, finished + 3600)
        self.assertIn("Nghỉ", reason)

    def test_failed_cleanup_blocks_after_midnight(self):
        self.state.launch(area(), "schedule")
        self.state.begin(run_id=42, created_at=self.now)
        persist_finish(self.host, self.state, False, False)
        self.host.existing = {"cleanup_confirmed_at": None}
        dispatch(self.host, self.state, timestamp("2026-10-11T00:01:00"))
        self.assertEqual(self.host.started, 0)
        self.assertIn("'cleanup_failed'", self.host.sql[-1])

    def test_preflight_failure_distinct_from_crawl_and_cleanup(self):
        self.state.launch(area(), "schedule")
        self.state.begin(run_id=42, created_at=self.now)
        self.state.progress("vpn_preflight_failed", status="failed")
        self.state.progress("vpn_cleanup")
        persist_finish(self.host, self.state, False, True)
        self.assertIn("'preflight_failed'", self.host.sql[-1])
        self.assertTrue(self.state.get("pipeline")["cleanup_confirmed"])

    def test_shortfall_notice_once_per_day(self):
        class Notifier:
            calls = []

            def send_message(self, message):
                self.calls.append(message)

        notifier = Notifier()
        self.host.daily_value = {"runs": 5, "total_urls": 8000}
        dispatch(self.host, self.state, self.now, notifier)
        dispatch(self.host, ControlState(self.state.path), self.now + 60, notifier)
        self.assertEqual(len(notifier.calls), 1)
        self.assertIn("2000", notifier.calls[0])

    def test_new_day_resets_daily_budget(self):
        self.host.daily_value = {"runs": 5, "total_urls": 0}
        dispatch(self.host, self.state, self.now)
        self.host.daily_value = {"runs": 0, "total_urls": 0}
        dispatch(self.host, self.state, timestamp("2026-10-11T00:00:00"))
        self.assertEqual(self.host.started, 1)

    def test_parallel_confirmations_only_one_queue_and_nonce_one_use(self):
        nonce = self.state.confirmation(self.now, area())

        def accept(_):
            return ControlState(self.state.path).request_start(
                self.now + 1, nonce=nonce
            )

        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sum(pool.map(accept, range(8))), 1)
        first = self.state.get("start_request")
        nonce2 = self.state.confirmation(self.now + 2, area(2))
        self.assertFalse(self.state.request_start(self.now + 3, nonce=nonce2))
        self.assertEqual(self.state.get("start_request"), first)
        self.assertFalse(self.state.consume_confirmation(nonce2, self.now + 4))

    def test_confirmation_expiry_and_old_unaccepted_commands(self):
        nonce = self.state.confirmation(self.now, area())
        self.assertFalse(self.state.request_start(self.now + 120, nonce=nonce))
        self.assertIsNone(self.state.get("start_request"))


if __name__ == "__main__":
    unittest.main()
