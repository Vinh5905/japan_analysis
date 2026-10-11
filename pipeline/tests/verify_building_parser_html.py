"""Check real local HTML through the actual spider, using downloaded snapshots.

Run in the crawler image with the repository mounted and --html-dir pointing at
local fixtures. This command does not connect to SUUMO, source DB or MinIO.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "suumo_source_crawler/crawler"))
from scrapy.http import TextResponse
from crawler.spiders.suumo_page import SuumoPageSpider
from crawler.building_identity import extract_property_code, normalize_building_name


def verify(html_dir, report):
    """Assert each HTML result survives parser record creation and JSON encoding."""
    with patch("crawler.spiders.suumo_page.create_minio_client"):
        spider = SuumoPageSpider()
    rows = []
    for path in sorted(Path(html_dir).glob("*.html"), key=lambda p: int(p.stem)):
        html = path.read_text()
        response = TextResponse(
            "https://suumo.jp/chintai/fixture", body=html.encode(), encoding="utf-8"
        )
        record = json.loads(
            json.dumps(
                spider.build_parser_record(
                    int(path.stem), spider.extract_page_data(response)
                ),
                ensure_ascii=False,
            )
        )
        assert record["is_valid"], path
        assert record["building_name_parse_status"] == "parsed", path
        assert record["building_name_raw"], path
        assert str(record["SUUMO物件コード"]) == extract_property_code(html), path
        rows.append(
            {
                key: record[key]
                for key in (
                    "task_id",
                    "SUUMO物件コード",
                    "所在地",
                    "listing_headline_raw",
                    "building_name_raw",
                    "room_number_raw",
                    "building_name_parse_status",
                    "data_hash_version",
                )
            }
        )
    assert rows, "No HTML fixtures were found"
    indexed = {r["task_id"]: r for r in rows}
    if 8 in indexed:
        assert indexed[8]["building_name_raw"] == "プレリスNEO大阪十三エルヴィオン"
        assert indexed[8]["room_number_raw"] == "203"
    if 16 in indexed:
        assert indexed[16]["building_name_raw"] == "プレリスNEO大阪十三エルヴィオン"
    groups = {
        (normalize_building_name(r["building_name_raw"]), r["所在地"]) for r in rows
    }
    with Path(report).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "html_tested": len(rows),
                "names_extracted": len(rows),
                "named_address_candidates": len(groups),
                "rooms_extracted": sum(bool(r["room_number_raw"]) for r in rows),
            }
        )
    )


def main():
    """Expose a repeatable offline test over downloaded local snapshots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html-dir", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    verify(args.html_dir, args.report)


if __name__ == "__main__":
    main()
