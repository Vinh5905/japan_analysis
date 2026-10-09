"""Verify runtime environment overrides without network, MinIO or a database."""

import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


SETTINGS = Path(__file__).resolve().parents[1] / "crawler/crawler/settings.py"


class RuntimeSettingsTests(unittest.TestCase):
    """Ensure .env knobs actually reach the values consumed by Scrapy."""

    def load(self, environment):
        """Evaluate settings in a clean environment so tests cannot inherit secrets."""
        with patch.dict(os.environ, environment, clear=True):
            return runpy.run_path(str(SETTINGS))

    def test_default_behavior_is_preserved(self):
        """An unchanged VPS must keep its old search and pacing."""
        settings = self.load({})
        self.assertEqual(settings["CONCURRENT_REQUESTS"], 2)
        self.assertEqual(settings["CONCURRENT_REQUESTS_PER_DOMAIN"], 1)
        self.assertEqual(settings["AUTOTHROTTLE_TARGET_CONCURRENCY"], 0.5)
        self.assertEqual(settings["SUUMO_PAGE_BATCH_SIZE"], 100)
        self.assertIn("sc=27123", settings["SUUMO_SEARCH_URL"])

    def test_env_overrides_numeric_and_string_settings(self):
        """Limits, batching, shared links file and search can change without rebuilding."""
        settings = self.load({"SUUMO_HTML_LINK_LIMIT": "5", "SUUMO_PAGE_TASK_LIMIT": "7",
                              "SUUMO_PAGE_BATCH_SIZE": "10", "SUUMO_PAGE_BATCH_SECONDS": "20",
                              "SUUMO_HTML_LINKS_FILE": "tmp/custom.txt", "SUUMO_RUN_CREATED_BY": "manual",
                              "SUUMO_SOURCE_ID": "2", "SUUMO_SOURCE_BASE_URL": "https://suumo.jp",
                              "SUUMO_SEARCH_URL": "https://suumo.jp/example?a=1&b=2",
                              "SUUMO_CONCURRENT_REQUESTS": "3", "SUUMO_CONCURRENT_REQUESTS_PER_DOMAIN": "2",
                              "SUUMO_AUTOTHROTTLE_START_DELAY": "4", "SUUMO_AUTOTHROTTLE_MAX_DELAY": "30",
                              "SUUMO_AUTOTHROTTLE_TARGET_CONCURRENCY": "0.25"})
        self.assertEqual(settings["SUUMO_HTML_LINK_LIMIT"], 5)
        self.assertEqual(settings["SUUMO_PAGE_TASK_LIMIT"], 7)
        self.assertEqual(settings["SUUMO_PAGE_BATCH_SIZE"], 10)
        self.assertEqual(settings["SUUMO_PAGE_BATCH_SECONDS"], 20)
        self.assertEqual(settings["SUUMO_HTML_LINKS_FILE"], "tmp/custom.txt")
        self.assertEqual(settings["SUUMO_RUN_CREATED_BY"], "manual")
        self.assertEqual(settings["SUUMO_SOURCE_ID"], 2)
        self.assertEqual(settings["CONCURRENT_REQUESTS"], 3)
        self.assertEqual(settings["CONCURRENT_REQUESTS_PER_DOMAIN"], 2)
        self.assertEqual(settings["AUTOTHROTTLE_TARGET_CONCURRENCY"], 0.25)
        self.assertEqual(settings["SUUMO_SEARCH_URL"], "https://suumo.jp/example?a=1&b=2")

    def test_invalid_knobs_fail_before_crawling(self):
        """Reject zero-sized batches and invalid pacing instead of silently falling back."""
        for environment in ({"SUUMO_PAGE_BATCH_SIZE": "0"}, {"SUUMO_HTML_LINK_LIMIT": "-1"},
                            {"SUUMO_PAGE_BATCH_SECONDS": "bad"}, {"SUUMO_CONCURRENT_REQUESTS": "0"},
                            {"SUUMO_AUTOTHROTTLE_TARGET_CONCURRENCY": "nan"},
                            {"SUUMO_AUTOTHROTTLE_MAX_DELAY": "1"}):
            with self.subTest(environment=environment), self.assertRaises(ValueError):
                self.load(environment)


if __name__ == "__main__":
    unittest.main()
