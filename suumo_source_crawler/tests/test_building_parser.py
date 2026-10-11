"""Run against the actual spider with no crawler/network side effects."""

import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "crawler"))
from scrapy.http import TextResponse
from crawler.spiders.suumo_page import SuumoPageSpider, PARSER_RECORD_FIELD_NAMES
from crawler.storage import SUUMO_DATA_HASH_FIELDS, suumo_data_hash


class ParserBuildingTests(unittest.TestCase):
    """Verify helper output survives the fixed record schema and JSON encoding."""

    def setUp(self):
        """Instantiate the parser while preventing external client creation."""
        with patch("crawler.spiders.suumo_page.create_minio_client"):
            self.spider = SuumoPageSpider()

    def test_real_parser_record_round_trip(self):
        """A real response keeps building identity through extract/build/JSON."""
        html = '<h1 class="section_h1-header-title">テスト弐番館 203号室</h1><table class="property_view_table"><tr><th>所在地</th><td>大阪府大阪市淀川区十三本町２</td></tr></table>'
        response = TextResponse(
            "https://suumo.jp/chintai/example", body=html.encode(), encoding="utf-8"
        )
        record = json.loads(
            json.dumps(
                self.spider.build_parser_record(
                    1, self.spider.extract_page_data(response)
                ),
                ensure_ascii=False,
            )
        )
        self.assertEqual(set(record), set(PARSER_RECORD_FIELD_NAMES))
        self.assertTrue(record["is_valid"])
        self.assertEqual(record["building_name_raw"], "テスト弐番館")
        self.assertEqual(record["room_number_raw"], "203")
        self.assertEqual(record["data_hash_version"], 2)
        self.assertEqual(record["data_hash"], suumo_data_hash(record))

    def test_headline_alone_does_not_make_error_page_valid(self):
        """Building parse status is metadata, not evidence of valid detail data."""
        response = TextResponse(
            "https://suumo.jp/error", body=b"<title>SUUMO</title>", encoding="utf-8"
        )
        self.assertFalse(
            self.spider.build_parser_record(1, self.spider.extract_page_data(response))[
                "is_valid"
            ]
        )

    def test_legacy_hash_stability_and_new_identity_hash(self):
        """Preserve the byte-for-byte v1 algorithm; v2 tracks name/room changes."""
        record = {
            "所在地": "大阪府",
            "building_name_raw": "テスト",
            "room_number_raw": "203",
        }
        expected = hashlib.sha256(
            json.dumps(
                {k: record.get(k) for k in SUUMO_DATA_HASH_FIELDS},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        self.assertEqual(suumo_data_hash(record), expected)
        self.assertEqual(suumo_data_hash({**record, "data_hash_version": 1}), expected)
        v2 = {**record, "data_hash_version": 2}
        self.assertNotEqual(suumo_data_hash(v2), expected)
        self.assertNotEqual(
            suumo_data_hash(v2), suumo_data_hash({**v2, "room_number_raw": "204"})
        )


if __name__ == "__main__":
    unittest.main()
