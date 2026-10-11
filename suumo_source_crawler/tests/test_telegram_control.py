"""Offline acceptance checks: no real bot, systemd, VPN, SSH or database writes."""

import argparse
import contextlib
from datetime import datetime
from html.parser import HTMLParser
import io
import json
from html import unescape
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "crawler"))
from scripts.telegram_state import ControlState, state_for
from scripts.telegram_control import ApiError, Controller, Host, COMMANDS, poll
from scripts import run_release_pipeline as pipeline, stop_openvpn as shutdown
from crawler.telegram_notifier import build_event_message, TelegramNotifier
from scripts import telegram_ui as ui


AREA = {
    "area_id": 1,
    "prefecture": "大阪府",
    "district": None,
    "municipality": "大阪市",
    "ward": "淀川区",
    "sc": "27123",
    "display_name": "Yodogawa",
    "runs": 0,
    "last_run": None,
    "today_runs": 0,
    "search_url": "https://suumo.jp/chintai/?sc=27123",
}


def begin_test(state, source="schedule"):
    state.launch(AREA, source)
    return state.begin(run_id=42, created_at=1000)


def visible(message):
    import re

    return unescape(re.sub(r"<[^>]*>", "", message))


class Api:
    def __init__(self):
        self.calls = []

    def call(self, method, payload=None):
        self.calls.append((method, payload))
        return {"message_id": 10}

    @property
    def messages(self):
        return [
            payload["text"] for method, payload in self.calls if method == "sendMessage"
        ]


class FakeHost:
    def __init__(self, directory):
        self.env_file = directory / ".env"
        self.busy_value = False
        self.starts = 0
        self.source_id = 7
        self.values = {}
        self.rows = []

    def busy(self):
        return self.busy_value

    def wake(self):
        self.starts += 1

    def start(self):
        self.starts += 1

    def areas(self, now=None):
        return [AREA]

    def daily(self, now=None):
        return {"total_urls": 27, "runs": 3}

    def unresolved(self):
        return None

    def properties(self, *args):
        return {"ActiveState": "active"}

    def status(self, state):
        return {"Crawler": "đang chạy" if self.busy_value else "rảnh"}

    def total(self):
        return {"total_urls": 27, "runs": 3}

    def history(self):
        return self.rows

    def schedule(self):
        return {"Timer": "đã tắt"}


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.state = state_for(self.directory / ".env")
        self.api = Api()
        self.host = FakeHost(self.directory)
        self.bot = Controller(self.api, self.state, self.host, "123")
        self.update_id = 0

    def message(
        self, text="/run_crawl", sender=123, chat=123, kind="private", date=1000
    ):
        self.update_id += 1
        return {
            "update_id": self.update_id,
            "message": {
                "date": date,
                "text": text,
                "chat": {"id": chat, "type": kind},
                "from": {"id": sender},
            },
        }

    def callback(self, nonce, action="run", sender=123, chat=123, kind="private"):
        self.update_id += 1
        return {
            "update_id": self.update_id,
            "callback_query": {
                "id": str(self.update_id),
                "data": action + ":" + nonce,
                "from": {"id": sender},
                "message": {"message_id": 10, "chat": {"id": chat, "type": kind}},
            },
        }

    def prompt(self):
        self.bot.handle(self.message(), 1000)
        self.bot.handle(self.callback("1", action="pick"), 1000)
        payload = [p for method, p in self.api.calls if method == "editMessageText"][-1]
        return payload["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split(
            ":"
        )[1]

    def test_rejects_other_chat_sender_and_non_private_for_messages_and_callbacks(self):
        for args in ({"sender": 999}, {"chat": 999}, {"kind": "group"}):
            self.bot.handle(self.message(**args), 1000)
            nonce = self.state.confirmation(1000)
            self.bot.handle(self.callback(nonce, **args), 1001)
            self.assertTrue(self.state.consume_confirmation(nonce, 1002))
        self.assertEqual(self.host.starts, 0)
        self.assertEqual(self.api.calls, [])

    def test_confirm_is_one_use_even_after_restart_or_duplicate_update(self):
        nonce = self.prompt()
        update = self.callback(nonce)
        self.bot.handle(update, 1001)
        self.bot = Controller(self.api, ControlState(self.state.path), self.host, "123")
        self.bot.handle(update, 1002)
        self.bot.handle(self.callback(nonce), 1003)
        self.assertEqual(self.host.starts, 1)
        self.assertEqual(self.state.get("offset"), self.update_id + 1)
        self.assertEqual(self.state.path.stat().st_mode & 0o777, 0o600)

    def test_expired_and_cancelled_confirmation_never_starts(self):
        nonce = self.prompt()
        self.bot.handle(self.callback(nonce), 1120)
        nonce = self.prompt()
        self.bot.handle(self.callback(nonce, action="cancel"), 1001)
        self.bot.handle(self.callback(nonce), 1002)
        self.assertEqual(self.host.starts, 0)

    def test_new_prompt_invalidates_older_button(self):
        old, new = self.prompt(), self.prompt()
        self.bot.handle(self.callback(old), 1001)
        self.assertEqual(self.host.starts, 0)
        self.bot.handle(self.callback(new), 1002)
        self.assertEqual(self.host.starts, 1)

    def test_running_timer_between_prompt_and_confirmation_queues_one_ward(self):
        nonce = self.prompt()
        self.host.busy_value = True
        self.bot.handle(self.callback(nonce), 1001)
        self.assertEqual(self.host.starts, 1)
        self.assertEqual(self.state.get("start_request")["area"]["area_id"], 1)

    def test_request_pending_after_crash_does_not_expire(self):
        self.state.request_start(1000, AREA)
        self.assertTrue(self.bot.pending(1301))
        self.assertTrue(
            Controller(
                self.api, ControlState(self.state.path), self.host, "123"
            ).pending(100000)
        )
        self.assertFalse(self.state.request_start(100001, {**AREA, "area_id": 2}))

    def test_manual_source_consumed_once_at_preflight(self):
        self.state.request_start(1000, AREA)
        request = self.state.get("start_request")
        self.state.launch(AREA, "manual", request["id"], 1001)
        self.assertEqual(
            self.state.begin(run_id=42, created_at=1001)["source"], "manual"
        )
        self.assertIsNone(self.state.get("start_request"))
        with self.assertRaises(RuntimeError):
            self.state.begin(run_id=42, created_at=1002)

    def test_stale_run_command_rejected_after_restart(self):
        self.bot.handle(self.message(date=600), 1000)
        self.assertEqual(self.host.starts, 0)
        self.assertIn("đã cũ", self.api.messages[-1])

    def test_crash_after_persisting_offset_never_replays_start(self):
        nonce = self.prompt()
        update = self.callback(nonce)
        with patch.object(self.host, "wake", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.bot.handle(update, 1001)
        restarted = Controller(
            self.api, ControlState(self.state.path), self.host, "123"
        )
        restarted.handle(update, 1002)
        self.assertEqual(self.host.starts, 0)
        self.assertTrue(restarted.pending(1002))

    def test_queue_is_accepted_during_deploy_and_dispatch_wakes_later(self):
        from scripts.runtime_lock import release_lock

        nonce = self.prompt()
        with release_lock(self.directory):
            self.bot.handle(self.callback(nonce), 1001)
        self.assertEqual(self.host.starts, 1)
        self.assertTrue(self.state.get("start_request"))

    def test_can_view_status_history_total_while_crawler_is_running(self):
        self.host.busy_value = True
        for command in ("/status", "/history", "/total", "/schedule", "/help"):
            self.bot.handle(self.message(command), 1000)
        self.assertEqual(len(self.api.messages), 5)
        self.assertIn("URL đã xử lý: 27", visible(self.api.messages[2]))
        for command, _ in COMMANDS:
            self.assertIn("/" + command, self.api.messages[-1])

    def test_db_failure_is_unavailable_not_fabricated_zero(self):
        with patch.object(
            self.host, "total", side_effect=RuntimeError("DB unavailable")
        ):
            self.bot.handle(self.message("/total"), 1000)
        self.assertIn("Chưa lấy được", self.api.messages[-1])
        self.assertNotIn("URL đã xử lý: 0", visible(self.api.messages[-1]))

    def test_empty_history_and_zero_total_are_distinct_from_error(self):
        self.bot.handle(self.message("/history"), 1000)
        self.assertIn("Chưa có lượt", self.api.messages[-1])
        with patch.object(
            self.host, "total", return_value={"total_urls": 0, "runs": 0}
        ):
            self.bot.handle(self.message("/total"), 1000)
        self.assertIn("URL đã xử lý: 0", visible(self.api.messages[-1]))

    def test_history_formats_five_runs_with_failures_rerun_and_current_run(self):
        self.host.rows = [
            {
                "run_id": i,
                "created_at": "2026-10-09T00:00:00+00:00",
                "finished_at": None if i == 5 else "done",
                "created_by": "manual",
                "total_urls": i,
                "html_success": i - 1,
                "html_failed": 1,
            }
            for i in range(5, 0, -1)
        ]
        self.bot.handle(self.message("/history"), 1000)
        text = self.api.messages[-1]
        self.assertEqual(text.count("HTML thành công:"), 5)
        self.assertIn("09/10/2026 07:00", text)
        self.assertIn("đang tải HTML", text)
        self.assertIn("thất bại: 1", text)

    def test_send_failure_does_not_repeat_start(self):
        nonce = self.prompt()
        with patch.object(self.api, "call", side_effect=OSError("network")):
            self.bot.handle(self.callback(nonce), 1001)
        self.assertEqual(self.host.starts, 1)
        self.bot.handle(self.callback(nonce), 1002)
        self.assertEqual(self.host.starts, 1)

    def test_navigation_is_authorized_and_cannot_start_crawler(self):
        for args in ({"sender": 999}, {"chat": 999}, {"kind": "group"}):
            self.bot.handle(self.callback("total", action="view", **args), 1000)
        self.assertEqual(self.api.calls, [])
        for name in ui.VIEWS - {"run_crawl", "refresh_areas"}:
            self.bot.handle(self.callback(name, action="view"), 1001)
        self.assertEqual(self.host.starts, 0)
        self.assertIsNone(self.state.get("start_request"))
        self.assertFalse(any(method == "sendMessage" for method, _ in self.api.calls))

    def test_run_button_opens_confirmation_and_duplicate_navigation_is_ignored(self):
        update = self.callback("run_crawl", action="view")
        self.bot.handle(update, 1000)
        count = len(self.api.calls)
        self.bot.handle(update, 1001)
        self.assertEqual(len(self.api.calls), count)
        payload = [p for m, p in self.api.calls if m == "editMessageText"][-1]
        self.assertTrue(
            payload["reply_markup"]["inline_keyboard"][0][0][
                "callback_data"
            ].startswith("pick:")
        )
        self.bot.handle(self.callback("1", action="pick"), 1001)
        payload = [p for m, p in self.api.calls if m == "editMessageText"][-1]
        nonce = payload["reply_markup"]["inline_keyboard"][0][0]["callback_data"].split(
            ":"
        )[1]
        self.assertEqual(self.host.starts, 0)
        self.bot.handle(self.callback(nonce), 1002)
        self.assertEqual(self.host.starts, 1)

    def test_callback_acknowledged_before_query_and_error_edits_same_card(self):
        def query():
            self.assertEqual(self.api.calls[-1][0], "answerCallbackQuery")
            raise RuntimeError("DB down")

        with patch.object(self.host, "total", side_effect=query):
            self.bot.handle(self.callback("total", action="view"), 1000)
        edits = [p for m, p in self.api.calls if m == "editMessageText"]
        self.assertEqual(edits[-1]["message_id"], 10)
        self.assertIn("Chưa lấy được", edits[-1]["text"])
        self.assertEqual(self.api.messages, [])

    def test_unchanged_edit_does_not_send_duplicate_message(self):
        def call(method, payload):
            self.api.calls.append((method, payload))
            if method == "editMessageText":
                raise ApiError(400, "Bad Request: message is not modified")

        self.api.call = call
        self.bot.handle(self.callback("home", action="view"), 1000)
        self.assertEqual(self.api.messages, [])

    def test_deleted_message_edit_falls_back_to_new_card(self):
        def call(method, payload):
            self.api.calls.append((method, payload))
            if method == "editMessageText":
                raise ApiError(400, "Bad Request: message to edit not found")

        self.api.call = call
        self.bot.handle(self.callback("home", action="view"), 1000)
        self.assertEqual(len(self.api.messages), 1)

    def test_cancel_edits_prompt_and_removes_confirmation(self):
        nonce = self.prompt()
        self.bot.handle(self.callback(nonce, action="cancel"), 1001)
        edited = [p for m, p in self.api.calls if m == "editMessageText"][-1]
        self.assertIn("Đã hủy", edited["text"])
        self.assertFalse(self.state.consume_confirmation(nonce, 1002))
        self.assertEqual(len(self.api.messages), 1)
        self.assertEqual(self.host.starts, 0)

    def test_rendered_cards_escape_and_redact_config_secrets(self):
        self.host.values = {
            "POSTGRES_PASSWORD": "s&<private>",
            "SUUMO_HTML_LINK_LIMIT": "<script>s&<private></script>",
        }
        self.prompt()
        message = [p["text"] for m, p in self.api.calls if m == "editMessageText"][-1]
        self.assertNotIn("<script>", message)
        self.assertNotIn("s&amp;&lt;private&gt;", message)
        self.assertIn("[REDACTED]", message)

    def test_unknown_navigation_does_not_query_or_consume_confirmation(self):
        nonce = self.prompt()
        with patch.object(self.host, "total") as query:
            self.bot.handle(self.callback("total;run", action="view"), 1001)
        query.assert_not_called()
        self.assertTrue(self.state.consume_confirmation(nonce, 1002))
        self.assertEqual(self.host.starts, 0)


class InterfaceTests(unittest.TestCase):
    def test_mobile_keyboards_and_callback_byte_limits(self):
        for view in ui.VIEWS:
            rows = ui.keyboard(view)["inline_keyboard"]
            self.assertLessEqual(len(rows), 5)
            for row in rows:
                self.assertLessEqual(len(row), 2)
                for b in row:
                    self.assertLessEqual(len(b["callback_data"].encode("utf-8")), 64)
        with self.assertRaises(ValueError):
            ui.button("bad", "🔵" * 17)

    def test_history_card_is_bounded_and_has_five_runs(self):
        rows = [
            {
                "run_id": i,
                "created_at": "2026-10-09T00:00:00Z",
                "finished_at": "done",
                "created_by": "🔵" * 10000,
                "total_urls": 100000,
                "html_success": 99999,
                "html_failed": 1,
            }
            for i in range(8)
        ]
        message, _ = ui.history(rows, 1, 1000)
        self.assertEqual(message.count("HTML thành công:"), 5)
        self.assertLessEqual(len(message.encode("utf-16-le")) // 2, 4096)
        self.assertIn("09/10/2026 07:00", message)
        self.assertIn("100.000", message)

    def test_disabled_schedule_has_no_invented_next_run(self):
        message, _ = ui.schedule({"Timer": "đã tắt"}, 1000)
        self.assertIn("đã tắt", message)
        self.assertIn("chưa có", message)

    def test_schedule_uses_actual_calendar_and_converts_timezone(self):
        message, _ = ui.schedule(
            {
                "Timer": "đang bật",
                "Lịch thực tế": "{ OnCalendar=*-*-* 00:00:00 ; next_elapse=x }",
                "Lần kế tiếp (giờ Việt Nam)": "2026-10-09T17:00:00+00:00",
                "Timezone VPS": "UTC",
                "Tự bật khi boot": "enabled",
                "Còn lại": "60 phút",
            },
            1000,
        )
        self.assertIn("10/10/2026 00:00", message)
        self.assertIn("Timezone: UTC", message)
        self.assertIn("*-*-* 00:00:00", message)
        self.assertNotIn("next_elapse", message)


class HostTests(unittest.TestCase):
    def host(self, command):
        return Host(
            Path("/tmp/release/.env"),
            Path("/tmp/release/compose.yml"),
            {"SUUMO_SOURCE_ID": "7", "POSTGRES_USER": "user", "POSTGRES_DB": "db"},
            command,
        )

    def test_queries_scoped_ordered_limited_and_direct_sum(self):
        commands = []

        def command(args):
            commands.append(args)
            return "[]" if "json_agg" in args[-1] else '{"total_urls":27,"runs":3}'

        host = self.host(command)
        self.assertEqual(host.history(), [])
        self.assertEqual(host.total(), {"total_urls": 27, "runs": 3})
        self.assertIn("ORDER BY created_at DESC, run_id DESC LIMIT 5", commands[0][-1])
        self.assertIn("raw_snapshot_id IS NOT NULL", commands[0][-1])
        self.assertIn("SUM(total_urls)", commands[1][-1])
        for args in commands:
            self.assertIn("source_id=7", args[-1])
            self.assertIn("ON_ERROR_STOP=1", args)
            self.assertIn("postgres", args)
            self.assertIn("-X", args)

    def test_timer_uses_live_calendar_and_epoch_in_vietnam(self):
        def command(args):
            if args[0] == "busctl":
                self.assertIn("suumo_2dcrawler_2dpipeline_2etimer", args[3])
                return "t 1791504000000000"
            if args[0] == "timedatectl":
                return "UTC"
            return "LoadState=loaded\nActiveState=active\nUnitFileState=enabled\nTimersCalendar={ OnCalendar=Mon *-*-* 03:15:00 Europe/Berlin ; }\nNextElapseUSecRealtime=live"

        with patch("scripts.telegram_control.time.time", return_value=1791503940):
            fields = self.host(command).schedule()
        self.assertIn("Europe/Berlin", fields["Lịch thực tế"])
        self.assertIn("+07:00", fields["Lần kế tiếp (giờ Việt Nam)"])
        self.assertEqual(fields["Còn lại"], "1 phút")
        self.assertEqual(fields["Timezone VPS"], "UTC")

    def test_disabled_timer_has_no_next_run_even_if_timestamp_is_stale(self):
        def command(args):
            self.assertNotEqual(args[0], "busctl")
            return (
                "UTC"
                if args[0] == "timedatectl"
                else "LoadState=loaded\nActiveState=inactive\nNextElapseUSecRealtime=stale"
            )

        fields = self.host(command).schedule()
        self.assertEqual(fields["Timer"], "đã tắt")
        self.assertEqual(fields["Còn lại"], "chưa có")

    def test_invalid_source_cannot_inject_sql(self):
        with self.assertRaises(ValueError):
            Host(
                Path(".env"),
                Path("compose"),
                {"SUUMO_SOURCE_ID": "1; DROP TABLE crawl_runs"},
            )

    def test_systemd_busy_and_manual_container_busy(self):
        def command(args):
            if args[0] == "systemctl":
                return "LoadState=loaded\nActiveState=activating"
            raise AssertionError("must not query Docker when unit is busy")

        self.assertTrue(self.host(command).busy())

        def manual(args):
            if args[0] == "systemctl":
                return "LoadState=loaded\nActiveState=inactive"
            return '{"name":"release"}' if "config" in args else "postgres\nsuumo-html"

        self.assertTrue(self.host(manual).busy())

    def test_status_preserves_known_inactive_vpn_state(self):
        host = self.host(
            lambda args: self.fail("Inactive VPN needs no ip/route queries")
        )

        def properties(unit, names):
            return {"ActiveState": "inactive", "SubState": "dead", "Result": "success"}

        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(host, "busy", return_value=False),
            patch.object(host, "properties", side_effect=properties),
            patch.object(host, "schedule", return_value={"Timer": "đang bật"}),
        ):
            fields = host.status(state_for(Path(directory) / ".env"))
        self.assertIn("service state is inactive", fields["VPN"])
        self.assertNotIn("unknown", fields["VPN"])


class PollTests(unittest.TestCase):
    def test_webhook_is_not_deleted(self):
        api = Api()
        with patch.object(
            api, "call", return_value={"url": "https://example.org/hook"}
        ) as call:
            bot = type("Bot", (), {"api": api})()
            with self.assertRaises(ApiError):
                poll(bot, sleeper=lambda _: None)
            self.assertEqual(
                [args.args[0] for args in call.call_args_list], ["getWebhookInfo"]
            )

    def test_reconnect_with_backoff_and_saved_offset_and_menu_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_for(Path(directory) / ".env")
            state.accept_update(42)
            api = Api()
            sleeps = []
            calls = []

            def call(method, payload=None):
                calls.append((method, payload))
                if method == "getWebhookInfo":
                    return {"url": ""}
                if method == "setMyCommands":
                    return True
                if len(sleeps) < 2:
                    raise OSError("network down")
                return []

            api.call = call
            bot = Controller(api, state, FakeHost(Path(directory)), "123")
            polls = lambda: len([m for m, p in calls if m == "getUpdates"])
            poll(bot, sleeper=sleeps.append, stop=lambda: polls() == 3)
            self.assertGreater(sleeps[1], sleeps[0])
            self.assertEqual(
                [p["offset"] for m, p in calls if m == "getUpdates"], [43, 43, 43]
            )
            menu = [p for m, p in calls if m == "setMyCommands"][0]
            self.assertEqual(menu["scope"], {"type": "chat", "chat_id": "123"})


class FormattingAndLifecycleTests(unittest.TestCase):
    def test_html_escape_redaction_long_text_and_zero(self):
        message = build_event_message(
            "JOB BẮT ĐẦU",
            {"Job": "suumo_html", "Error": "<bad>& password=hunter2 " * 500, "URL": 0},
            possible_causes=["<hint>&" * 100] * 10,
        )
        self.assertIn("<b>", message)
        self.assertIn("📥", message)
        self.assertIn("&lt;bad&gt;&amp;", message)
        self.assertNotIn("hunter2", message)
        self.assertIn("URL: 0", message)
        self.assertLessEqual(len(message), 4096)

        class Check(HTMLParser):
            def handle_starttag(self, tag, attrs):
                self.assert_tag(tag)

        parser = Check()
        parser.assert_tag = lambda tag: self.assertEqual(tag, "b")
        parser.feed(message)
        self.assertEqual(message.count("<b>"), message.count("</b>"))

    def test_notification_redacts_env_secret_after_html_escape(self):
        notifier = TelegramNotifier.from_env(
            {
                "TELEGRAM_BOT_TOKEN": "123:token",
                "TELEGRAM_CHAT_ID": "123",
                "POSTGRES_PASSWORD": "S&<secret>",
            }
        )
        from test_telegram_notifications import FakeHttpResponse

        with patch(
            "crawler.telegram_notifier.urlopen", return_value=FakeHttpResponse()
        ) as request:
            notifier.send_message(
                build_event_message("FAILED", {"Error": "S&<secret>"})
            )
        payload = json.loads(request.call_args.args[0].data)
        self.assertNotIn("S&amp;", payload["text"])
        self.assertEqual(payload["parse_mode"], "HTML")

    def test_short_secret_cannot_corrupt_html_tags(self):
        from crawler.telegram_notifier import prepare_html, load_telegram_config

        config = load_telegram_config({"POSTGRES_PASSWORD": "b"})
        prepared = prepare_html(build_event_message("TEST", {"Value": "b"}), config)
        self.assertIn("<b>", prepared)
        self.assertIn("</b>", prepared)
        self.assertIn("[REDACTED]", prepared)

    def test_long_emoji_messages_fit_utf16_limit(self):
        message = build_event_message("TEST", {str(i): "🔵" * 1000 for i in range(30)})
        self.assertLessEqual(len(message.encode("utf-16-le")) // 2, 4096)
        self.assertIn("</b>", message)

    def test_state_read_failure_still_closes_vpn(self):
        args = argparse.Namespace(
            env_file=Path(".env"),
            compose_file=Path("compose"),
            lock_held=True,
            service="openvpn-client@japan",
            interface="tun0",
            stop_attempts=3,
            checks_per_attempt=3,
            required_consecutive_checks=3,
            check_interval_seconds=0,
        )
        with (
            patch.object(shutdown, "parse_args", return_value=args),
            patch.object(shutdown, "read_env_file", return_value={}),
            patch.object(shutdown, "state_for", side_effect=OSError("disk full")),
            patch.object(shutdown, "finish_crawler_containers"),
            patch.object(shutdown, "stop_vpn", return_value=True) as stop,
            patch.dict(os.environ, {}, clear=True),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(shutdown.main(), 0)
        stop.assert_called_once()

    def test_pipeline_defers_completion_and_manual_source_reaches_image(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            env = base / ".env"
            env.write_text("TELEGRAM_BOT_TOKEN=\nSUUMO_RUN_CREATED_BY=schedule\n")
            state = state_for(env)
            run = begin_test(state, "manual")
            state.progress("vpn_ready", vpn={"vpn_id": 1, "filename": "qa.ovpn"})
            args = argparse.Namespace(env_file=env, compose_file=base / "compose.yml")
            notifier = Api()
            notifier.send_message = lambda m: notifier.calls.append(("message", m))
            commands = []

            def command(args, cwd, values):
                commands.append(args)
                name = args[-1].replace("-", "_")
                if name in pipeline.SPIDER_NAMES:
                    summary_dir = base / "tmp/telegram" / run["run_id"]
                    summary_dir.mkdir(parents=True, exist_ok=True)
                    (summary_dir / (name + ".json")).write_text(
                        json.dumps(
                            {
                                "job_name": name,
                                "status": "completed",
                                "close_reason": "finished",
                            }
                        )
                    )
                return pipeline.CommandResult(0, "")

            with (
                patch.object(
                    pipeline.TelegramNotifier, "from_env", return_value=notifier
                ),
                patch.object(pipeline, "run_command", side_effect=command),
                contextlib.redirect_stdout(io.StringIO()),
                patch.dict(os.environ, {}, clear=True),
            ):
                self.assertEqual(pipeline.run_pipeline(args), 0)
            self.assertFalse(any("HOÀN THÀNH" in m for _, m in notifier.calls))
            self.assertTrue(state.get("pipeline")["completion"])
            self.assertTrue(
                any("SUUMO_RUN_CREATED_BY=manual" in command for command in commands)
            )
            self.assertEqual(state.get("pipeline")["run_id"], run["run_id"])

    def test_pipeline_refuses_context_before_vpn_preflight_has_passed(self):
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / ".env"
            env.write_text("")
            begin_test(state_for(env))
            args = argparse.Namespace(env_file=env, compose_file=env.parent / "compose")
            with (
                patch.object(pipeline, "run_command") as command,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(pipeline.run_pipeline(args), 2)
            command.assert_not_called()

    def test_cleanup_completion_only_after_confirmed_shutdown(self):
        for stopped in (True, False):
            with (
                self.subTest(stopped=stopped),
                tempfile.TemporaryDirectory() as directory,
            ):
                env = Path(directory) / ".env"
                env.write_text("")
                state = state_for(env)
                begin_test(state)
                state.progress(
                    "awaiting_vpn_cleanup",
                    completion={
                        "summaries": {},
                        "started_at": "now",
                        "hostname": "local",
                    },
                )
                args = argparse.Namespace(
                    env_file=env,
                    compose_file=env.parent / "compose",
                    lock_held=True,
                    service="openvpn-client@japan",
                    interface="tun0",
                    stop_attempts=3,
                    checks_per_attempt=3,
                    required_consecutive_checks=3,
                    check_interval_seconds=0,
                )
                messages = []
                notifier = type(
                    "Notifier", (), {"send_message": lambda self, m: messages.append(m)}
                )()

                def stop(*args, **kwargs):
                    self.assertFalse(
                        any("PIPELINE HOÀN THÀNH" in message for message in messages)
                    )
                    return stopped

                with (
                    patch.object(shutdown, "parse_args", return_value=args),
                    patch.object(
                        shutdown.TelegramNotifier, "from_env", return_value=notifier
                    ),
                    patch.object(shutdown, "finish_crawler_containers"),
                    patch.object(shutdown, "stop_vpn", side_effect=stop),
                    patch("scripts.crawl_dispatcher.persist_finish"),
                    patch("scripts.crawl_dispatcher.wake"),
                    patch.dict(os.environ, {"SERVICE_RESULT": "success"}, clear=True),
                ):
                    self.assertEqual(shutdown.main(), 0 if stopped else 1)
                self.assertEqual(
                    any("PIPELINE HOÀN THÀNH" in m for m in messages), stopped
                )
                self.assertIsNone(state.get("pipeline")["completion"])


if __name__ == "__main__":
    unittest.main()
