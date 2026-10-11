"""Fixture regressions for shared headline extraction and safe backfill."""

import gzip
import hashlib
import unittest
from unittest.mock import Mock

from crawler.building_identity import (
    extract_building_identity,
    extract_property_code,
    normalize_building_name,
)
from loaders.suumo_building_backfill import read_snapshot


class BuildingExtractionTests(unittest.TestCase):
    """Check only explicit room suffixes and recognizable SUUMO headings."""

    def test_room_suffix_and_wing_names(self):
        """Keep wing identifiers while separating an explicitly labeled room."""
        for heading, name, room in [
            (
                "プレリスNEO大阪十三エルヴィオン 203号室",
                "プレリスNEO大阪十三エルヴィオン",
                "203",
            ),
            ("セレニテ新大阪ミラク　弐番館", "セレニテ新大阪ミラク 弐番館", None),
            ("テスト1号棟 II", "テスト1号棟 II", None),
            ("テスト２０３号室", "テスト", "203"),
        ]:
            with self.subTest(heading=heading):
                result = extract_building_identity(
                    f'<h1 class="section_h1-header-title"><span>{heading}</span></h1>'
                )
                self.assertEqual(result["building_name_raw"], name)
                self.assertEqual(result["room_number_raw"], room)
                self.assertEqual(result["building_name_parse_status"], "parsed")

    def test_title_fallback_and_missing_generic_error(self):
        """Accept the SUUMO listing title format, never generic/error pages."""
        result = extract_building_identity(
            "<title>【SUUMO】テストマンション ２０３号室／大阪府大阪市／賃貸情報</title>"
        )
        self.assertEqual(result["building_name_raw"], "テストマンション")
        self.assertEqual(result["room_number_raw"], "203")
        self.assertEqual(result["building_name_source"], "title")
        for title in (
            "",
            "<title>SUUMO</title>",
            '<h1 class="section_h1-header-title">地下鉄御堂筋線 新大阪駅 徒歩5分</h1>',
            '<h1 class="section_h1-header-title">賃貸マンション</h1>',
            '<h1 class="section_h1-header-title">阪急京都線 十三駅 15階建 築5年</h1>',
            '<h1 class="section_h1-header-title">ページが見つかりません</h1>',
        ):
            self.assertIsNone(extract_building_identity(title)["building_name_raw"])

    def test_canonical_names_and_code(self):
        """NFKC/space/case are equivalent, but wing suffixes stay distinct."""
        self.assertEqual(
            normalize_building_name("Ｗｅｓｔ　Gate"),
            normalize_building_name("West Gate"),
        )
        self.assertNotEqual(
            normalize_building_name("テスト弐番館"),
            normalize_building_name("テスト壱番館"),
        )
        self.assertEqual(
            extract_property_code('<input value="123" id="clipkey">'), "123"
        )
        self.assertEqual(
            extract_property_code('<input name="clipkey" value="123">'), "123"
        )

    def test_snapshot_integrity_and_response_closed(self):
        """Check the original HTML hash and always close MinIO responses."""
        payload = "<title>テスト</title>".encode()
        response = Mock()
        response.read.return_value = gzip.compress(payload)
        client = Mock()
        client.get_object.return_value = response
        row = {
            "storage_path": "suumo/page_source/a.html.gz",
            "compression": "gzip",
            "content_hash": hashlib.sha256(payload).hexdigest(),
            "encoding": "utf-8",
        }
        self.assertEqual(read_snapshot(client, row), payload.decode())
        response.close.assert_called_once()
        response.release_conn.assert_called_once()
        row["content_hash"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            read_snapshot(client, row)


if __name__ == "__main__":
    unittest.main()
