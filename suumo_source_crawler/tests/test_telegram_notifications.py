from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "crawler"))

try:
    import scrapy  # noqa: F401
except ModuleNotFoundError:
    scrapy_module = types.ModuleType("scrapy")
    scrapy_module.signals = types.SimpleNamespace(
        spider_opened=object(),
        item_scraped=object(),
        spider_error=object(),
        spider_closed=object(),
        engine_stopped=object(),
    )
    sys.modules["scrapy"] = scrapy_module

from crawler.telegram_extension import (  # noqa: E402
    TelegramErrorBufferHandler,
    TelegramNotificationExtension,
)
from crawler.telegram_notifier import (  # noqa: E402
    TelegramConfig,
    TelegramNotifier,
    build_event_message,
    infer_possible_causes,
    load_telegram_config,
    truncate_message,
)
from scripts.run_release_pipeline import (  # noqa: E402
    CommandResult,
    pipeline_completed_message,
    pipeline_failed_message,
    read_env_file,
)


class FakeHttpResponse:
    def __init__(self, status_code: int = 200, payload: bytes = b'{"ok": true}'):
        self.status_code = status_code
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def getcode(self) -> int:
        return self.status_code

    def read(self) -> bytes:
        return self.payload


class CapturingNotifier:
    def __init__(self):
        self.messages: list[str] = []

    def send_message(self, message: str):
        self.messages.append(message)
        return None


class FakeSignals:
    def connect(self, receiver, signal):
        return None


class FakeStats:
    def __init__(self, values=None):
        self.values = values or {}

    def get_stats(self):
        return dict(self.values)


class FakeCrawler:
    def __init__(self, stats=None):
        self.signals = FakeSignals()
        self.stats = FakeStats(stats)


class FakeSpider:
    def __init__(self, name: str):
        self.name = name
        self.seen_url_hashes: set[str] = set()


class TelegramNotifierTests(unittest.TestCase):
    def test_missing_environment_disables_notifier(self):
        config = load_telegram_config({})

        self.assertFalse(config.enabled)
        result = TelegramNotifier(config).send_message("test")
        self.assertFalse(result.configured)
        self.assertFalse(result.sent)

    @patch("crawler.telegram_notifier.urlopen")
    def test_send_message_uses_bot_api_payload_and_timeout(self, mocked_urlopen):
        mocked_urlopen.return_value = FakeHttpResponse()
        notifier = TelegramNotifier(
            TelegramConfig(
                bot_token="123456:test-token",
                chat_id="987654",
                timeout_seconds=3.5,
            )
        )

        result = notifier.send_message("Crawler started")

        self.assertTrue(result.sent)
        request = mocked_urlopen.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/sendMessage"))
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["chat_id"], "987654")
        self.assertEqual(payload["text"], "Crawler started")
        self.assertEqual(mocked_urlopen.call_args.kwargs["timeout"], 3.5)

    @patch("crawler.telegram_notifier.urlopen", side_effect=URLError("network down"))
    def test_transport_failure_is_returned_without_raising(self, mocked_urlopen):
        notifier = TelegramNotifier(TelegramConfig("123:test", "987"))

        result = notifier.send_message("Crawler failed")

        self.assertFalse(result.sent)
        self.assertEqual(result.error_type, "URLError")
        mocked_urlopen.assert_called_once()

    def test_message_builder_redacts_token_and_enforces_limit(self):
        token = "123456:secret-token"
        message = build_event_message(
            "FAILED",
            {"Error": f"request /bot{token}/sendMessage failed"},
            bot_token=token,
        )

        self.assertNotIn(token, message)
        self.assertLessEqual(len(truncate_message("x" * 5000)), 4096)

    def test_cause_inference_distinguishes_network_and_suumo_blocking(self):
        causes = infer_possible_causes(
            "DNSLookupError timeout downloader/response_status_count/403"
        )

        self.assertTrue(any("DNS" in cause for cause in causes))
        self.assertTrue(any("VPN" in cause for cause in causes))
        self.assertTrue(any("SUUMO" in cause for cause in causes))


class TelegramExtensionTests(unittest.TestCase):
    def test_logging_handler_buffers_only_error_records_from_logger(self):
        logger = logging.getLogger("test.telegram.buffer")
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        handler = TelegramErrorBufferHandler()
        logger.addHandler(handler)
        self.addCleanup(logger.removeHandler, handler)

        logger.info("normal info")
        logger.warning("normal warning")
        logger.error("fatal database error")

        self.assertEqual(len(handler.records), 1)
        self.assertEqual(handler.latest["error_message"], "fatal database error")

    def test_links_zero_result_is_warning_and_summary_is_persisted(self):
        crawler = FakeCrawler(
            {
                "downloader/request_count": 1,
                "downloader/response_count": 1,
            }
        )
        extension = TelegramNotificationExtension(crawler)
        self.addCleanup(extension.engine_stopped)
        notifier = CapturingNotifier()
        extension.notifier = notifier
        spider = FakeSpider("suumo_links")

        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_PIPELINE_RUN_ID": "test-run",
                    "TELEGRAM_SUMMARY_DIR": temporary_directory,
                },
                clear=False,
            ):
                extension.spider_opened(spider)
                extension.spider_closed(spider, "finished")

            summary_path = Path(temporary_directory) / "test-run" / "suumo_links.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        self.assertEqual(summary["status"], "warning")
        self.assertEqual(summary["new_links"], 0)
        self.assertIn("Không tìm thấy URL", summary["warning_message"])
        self.assertEqual(len(notifier.messages), 2)
        self.assertIn("JOB BẮT ĐẦU", notifier.messages[0])
        self.assertIn("CÓ CẢNH BÁO", notifier.messages[1])

    def test_page_items_are_aggregated_without_modifying_them(self):
        crawler = FakeCrawler()
        extension = TelegramNotificationExtension(crawler)
        self.addCleanup(extension.engine_stopped)
        extension.notifier = CapturingNotifier()
        spider = FakeSpider("suumo_page")
        item = {
            "row_count": 5,
            "valid_count": 4,
            "invalid_count": 1,
        }

        extension.spider_opened(spider)
        extension.item_scraped(item, None, spider)
        summary = extension._build_summary(spider, "finished")
        extension.engine_stopped()

        self.assertEqual(item["row_count"], 5)
        self.assertEqual(summary.parsed_record_count, 5)
        self.assertEqual(summary.valid_record_count, 4)
        self.assertEqual(summary.invalid_record_count, 1)
        self.assertEqual(summary.batch_count, 1)


class ReleasePipelineTests(unittest.TestCase):
    def test_env_reader_supports_comments_export_and_quotes(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            env_path = Path(temporary_directory) / ".env"
            env_path.write_text(
                "# comment\nexport TELEGRAM_BOT_TOKEN='dummy-token'\n"
                'TELEGRAM_CHAT_ID="12345"\n',
                encoding="utf-8",
            )

            values = read_env_file(env_path)

        self.assertEqual(values["TELEGRAM_BOT_TOKEN"], "dummy-token")
        self.assertEqual(values["TELEGRAM_CHAT_ID"], "12345")

    def test_pipeline_failure_contains_required_context_and_hint(self):
        message = pipeline_failed_message(
            step_name="suumo-links",
            result=CommandResult(
                return_code=1,
                output_tail="DNSLookupError: request timed out",
            ),
            started_at="2026-09-16T19:00:00+07:00",
            duration_seconds=12.3,
            hostname="vps-host",
        )

        self.assertIn("PIPELINE THẤT BẠI", message)
        self.assertIn("CommandFailed", message)
        self.assertIn("vps-host", message)
        self.assertIn("DNS", message)
        self.assertIn("VPN", message)

    def test_pipeline_completion_aggregates_spider_counts(self):
        message = pipeline_completed_message(
            summaries={
                "suumo_links": {"new_links": 10},
                "suumo_html": {
                    "html_success_count": 9,
                    "html_failed_count": 1,
                },
                "suumo_page": {
                    "parsed_record_count": 9,
                    "valid_record_count": 8,
                    "invalid_record_count": 1,
                    "batch_count": 1,
                },
            },
            started_at="2026-09-16T19:00:00+07:00",
            duration_seconds=60,
            hostname="vps-host",
        )

        self.assertIn("Các bước hoàn thành: 3/3", message)
        self.assertIn("URL mới: 10", message)
        self.assertIn("HTML thành công: 9", message)
        self.assertIn("Records valid: 8", message)


if __name__ == "__main__":
    unittest.main()
