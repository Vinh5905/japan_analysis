"""Temporary QA database loader and comparator for the notebook snapshot."""

import csv
import json
import os
import sys
from datetime import datetime

import psycopg

DBNAME = "qa_suumo_history"
DATA_DIR = "/qa-data"
FIELD_MAP = {
    "suumo_property_code": "SUUMO物件コード",
    "shop_property_code": "取り扱い店舗物件コード",
    "information_updated_at_text": "情報更新日",
    "move_in": "入居",
    "transaction_type": "取引態様",
    "contract_period": "契約期間",
    "address": "所在地",
    "station_access": "駅徒歩",
    "rent_price_text": "家賃",
    "management_fee_text": "管理費_共益費",
    "other_monthly_costs": "ほか諸費用",
    "deposit_text": "敷金",
    "key_money_text": "礼金",
    "guarantee_deposit_text": "保証金",
    "depreciation_text": "敷引_償却",
    "brokerage_fee": "仲介手数料",
    "other_initial_costs": "ほか初期費用",
    "guarantee_company": "保証会社",
    "layout": "間取り",
    "layout_detail": "間取り詳細",
    "exclusive_area_text": "専有面積",
    "building_age_text": "築年数",
    "built_at_text": "築年月",
    "floor_text": "階",
    "building_floors": "階建",
    "total_units": "総戸数",
    "building_type": "建物種別",
    "structure": "構造",
    "direction": "向き",
    "conditions": "条件",
    "insurance": "損保",
    "parking": "駐車場",
    "energy_efficiency": "エネルギー消費性能",
    "insulation_performance": "断熱性能",
    "estimated_utility_cost": "目安光熱費",
    "remarks": "備考",
}


def connect(dbname: str, autocommit: bool = False) -> psycopg.Connection:
    """Connect to the local warehouse server without exposing credentials."""

    return psycopg.connect(
        host=os.environ["WAREHOUSE_POSTGRES_HOST"],
        port=os.environ["WAREHOUSE_POSTGRES_PORT"],
        user=os.environ["PIPELINE_POSTGRES_USER"],
        password=os.environ["PIPELINE_POSTGRES_PASSWORD"],
        dbname=dbname,
        autocommit=autocommit,
    )


def setup() -> None:
    """Load the offline raw CSV only into an isolated QA database."""

    with connect(os.environ["WAREHOUSE_DB"], autocommit=True) as admin:
        admin.execute(f"CREATE DATABASE {DBNAME}")
    with connect(DBNAME) as qa:
        qa.execute("CREATE SCHEMA raw")
        qa.execute("""CREATE TABLE raw.suumo_parser_records (
            task_id bigint primary key, batch_id bigint, source_id bigint,
            data_hash text, record jsonb, loaded_at timestamptz)""")
        with qa.cursor() as cur:
            with cur.copy("COPY raw.suumo_parser_records (task_id,batch_id,source_id,data_hash,record,loaded_at) FROM STDIN") as copy:
                with open(f"{DATA_DIR}/suumo_parser_records_raw.csv", encoding="utf-8-sig") as handle:
                    for row in csv.DictReader(handle):
                        record = {jp: row.get(en) or None for en, jp in FIELD_MAP.items()}
                        record.update(task_id=int(row["task_id"]), data_hash=row["data_hash"],
                                      is_valid=row["is_valid"].lower() == "true",
                                      parsed_at=row["parsed_at"] or None)
                        copy.write_row((int(row["task_id"]), int(row["batch_id"]),
                                        int(row["source_id"]), row["data_hash"],
                                        json.dumps(record, ensure_ascii=False),
                                        "2026-01-01T00:00:00Z"))
    print("Loaded QA raw CSV")


def compare() -> None:
    """Compare history and parsed station lines with the notebook snapshot."""

    with open(f"{DATA_DIR}/suumo_parser_records_clean.csv", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        expected = {int(row["task_id"]): row for row in reader}
    with connect(DBNAME) as qa:
        with qa.cursor() as cur:
            cur.execute("SELECT * FROM intermediate.int_suumo_rentals_history ORDER BY task_id")
            columns = [item.name for item in cur.description]
            comparison_columns = [column for column in columns if column != "record_origin"]
            missing_columns = set(comparison_columns) - set(next(iter(expected.values())))
            if len(columns) != 112 or missing_columns:
                raise AssertionError(f"Unexpected history columns: {len(columns)}, missing in snapshot: {missing_columns}")
            counts = {column: 0 for column in comparison_columns}
            samples = {}
            rows = 0
            for values in cur:
                actual = dict(zip(columns, values))
                target = expected[int(actual["task_id"])]
                rows += 1
                for column in comparison_columns:
                    left = str(actual[column]) if actual[column] is not None else ""
                    right = target[column]
                    if column == "quality_issue_count":
                        # Station failures now live only in the detail table.
                        right = str(int(right) - int(target["flag_station_parse_failure"].lower() == "true"))
                    if left.lower() in {"true", "false"}:
                        left = left.lower()
                        right = right.lower()
                    if column == "parsed_at_utc" and left and right:
                        left = datetime.fromisoformat(left).timestamp()
                        right = datetime.fromisoformat(right).timestamp()
                    if left != right and not (
                        left and right and column not in {"task_id", "batch_id", "source_id"}
                        and _same_number(str(left), str(right))
                    ):
                        counts[column] += 1
                        samples.setdefault(column, (actual["task_id"], left[:70], right[:70]))
    print(f"QA rows: {rows}; expected: {len(expected)}")
    print("Mismatch counts:")
    for column, count in counts.items():
        if count:
            print(column, count, samples[column])
    if rows != len(expected) or any(counts.values()):
        raise AssertionError("QA intermediate history differs from notebook clean history")
    compare_stations()


def compare_stations() -> None:
    """Compare valid station detail against the notebook's station export."""

    with open(f"{DATA_DIR}/suumo_station_access.csv", encoding="utf-8-sig") as handle:
        expected = {
            (int(row["task_id"]), int(row["access_order"])): row
            for row in csv.DictReader(handle)
        }
    with connect(DBNAME) as qa:
        with qa.cursor() as cur:
            cur.execute("""SELECT task_id, batch_id, suumo_property_code, access_order,
                                  station_line, station_name, access_mode, total_travel_minutes
                           FROM intermediate.int_suumo__station_access
                           WHERE parse_status = 'parsed' ORDER BY task_id, access_order""")
            columns = [item.name for item in cur.description]
            rows = 0
            for values in cur:
                actual = dict(zip(columns, values))
                key = (actual["task_id"], actual["access_order"])
                target = expected.get(key)
                if target is None:
                    raise AssertionError(f"Unexpected parsed station line: {key}")
                for column in columns:
                    if str(actual[column]) != target[column]:
                        raise AssertionError(
                            f"Station {key} {column}: {actual[column]!r} != {target[column]!r}"
                        )
                rows += 1
    print(f"QA parsed station rows: {rows}; expected: {len(expected)}")
    if rows != len(expected):
        raise AssertionError("QA station detail differs from notebook station export")


def _same_number(left: str, right: str) -> bool:
    """Compare CSV numeric formatting without losing exact field semantics."""

    try:
        return abs(float(left) - float(right)) <= 1e-8 * max(1, abs(float(right)))
    except ValueError:
        return False


def fixtures() -> None:
    """Add two boundary-case parser records to the isolated QA database."""

    records = [
        {
            "task_id": 1000001, "家賃": "８．１５万円", "管理費_共益費": "-",
            "専有面積": "２５．６６㎡", "階": "1-3階", "階建": "3階建",
            "築年数": "築９９年以上", "築年月": "2008年",
            "駅徒歩": "阪急宝塚線/十三駅 バス8分 (バス停)加島中 歩3分\ninvalid",
            "間取り": "2SLDK", "間取り詳細": "洋6.1 K2 ロフト 1.8-1.8",
            "損保": "１．８万円２年", "駐車場": "近隣200m22000円",
            "入居": "'26年9月初旬", "契約期間": "定期借家 5年4ヶ月",
            "所在地": "大阪府大阪市淀川区東三国2丁目",
        },
        {
            "task_id": 1000002, "家賃": "-", "管理費_共益費": "不要",
            "専有面積": "0m2", "階": "3-1階", "階建": "平屋",
            "築年月": "2026年7月", "間取り": "ワンルーム",
            "間取り詳細": "-", "損保": "不要", "駐車場": "付無料",
            "入居": "相談", "契約期間": "普通借家 2年",
        },
        {
            "task_id": 1000003, "駅徒歩": "ＪＲ線／大阪駅 歩５分\n\nＪＲ線／大阪駅 歩６分",
            "間取り詳細": "洋6 K2",
        },
    ]
    with connect(DBNAME) as qa:
        for record in records:
            record.update(is_valid=True, data_hash="a" * 64,
                          parsed_at="2026-08-04T00:16:39+00:00")
            qa.execute("""INSERT INTO raw.suumo_parser_records
                (task_id,batch_id,source_id,data_hash,record,loaded_at)
                VALUES (%s,1,1,%s,%s,'2026-08-04T00:16:39Z')
                ON CONFLICT (task_id) DO UPDATE SET record=excluded.record""",
                (record["task_id"], record["data_hash"], json.dumps(record, ensure_ascii=False)))
    print("Added QA fixtures")


def check_fixtures() -> None:
    """Assert the main edge cases match notebook parser semantics."""

    expected = {
        1000001: {
            "rent_jpy": 81500, "management_fee_jpy": 0,
            "exclusive_area_m2": 25.66, "floor_min": 1, "floor_max": 3,
            "floor_number": None, "building_age_years": 99,
            "building_age_is_lower_bound": True, "built_at_precision": "year",
            "layout_normalized": "2SLDK", "layout_has_service_room": True,
            "layout_detail_parse_status": "partial", "layout_detail_parse_failure_count": 1,
            "loft_present": True, "loft_size_jo": None,
            "insurance_jpy": 18000, "insurance_period_years": 2,
            "parking_location": "nearby", "parking_distance_m": 200,
            "parking_fee_jpy": 22000, "move_in_month": "2026-09",
            "move_in_period": "early", "contract_type": "fixed_term",
            "contract_years": 5, "contract_months": 4,
            "prefecture": "大阪府", "municipality": "大阪市", "ward": "淀川区",
            "locality": "東三国", "chome": 2,
            "quality_issue_count": 1,
        },
        1000002: {
            "rent_jpy": None, "management_fee_jpy": 0,
            "exclusive_area_m2": None, "floor_min": None,
            "built_at_precision": "month", "layout_normalized": "1R",
            "layout_detail_parse_status": "missing",
            "insurance_required": False, "parking_fee_jpy": 0,
            "move_in_status": "consultation", "contract_type": "ordinary",
            "contract_years": 2, "contract_months": 0,
            "flag_missing_core": True,
        },
        1000003: {
            "layout_detail_parse_status": "full", "layout_space_count": 2,
            "flag_missing_core": True,
        },
    }
    with connect(DBNAME) as qa:
        with qa.cursor() as cur:
            cur.execute("SELECT * FROM intermediate.int_suumo_rentals_history WHERE task_id IN (1000001,1000002,1000003)")
            columns = [item.name for item in cur.description]
            for values in cur:
                actual = dict(zip(columns, values))
                for name, value in expected[actual["task_id"]].items():
                    if actual[name] != value and not (
                        actual[name] is not None and value is not None
                        and not isinstance(value, bool)
                        and _same_number(str(actual[name]), str(value))
                    ):
                        raise AssertionError(f"{actual['task_id']} {name}: {actual[name]!r} != {value!r}")
            cur.execute("""SELECT task_id, access_order, raw_line, parse_status,
                                  station_line, station_name, access_mode, total_travel_minutes
                           FROM intermediate.int_suumo__station_access
                           WHERE task_id IN (1000001,1000002,1000003)
                           ORDER BY task_id, access_order""")
            station_rows = cur.fetchall()
            expected_stations = [
                (1000001, 1, "阪急宝塚線/十三駅 バス8分 (バス停)加島中 歩3分", "parsed", "阪急宝塚線", "十三", "bus", 11),
                (1000001, 2, "invalid", "unparsed", None, None, None, None),
                (1000003, 1, "ＪＲ線／大阪駅 歩５分", "parsed", "JR線", "大阪", "walk", 5),
                (1000003, 2, "ＪＲ線／大阪駅 歩６分", "parsed", "JR線", "大阪", "walk", 6),
            ]
            if station_rows != expected_stations:
                raise AssertionError(f"Station fixtures differ: {station_rows!r}")
    print("QA fixtures passed")


def teardown() -> None:
    """Remove the isolated QA database after comparison."""

    with connect(os.environ["WAREHOUSE_DB"], autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {DBNAME} WITH (FORCE)")
    print("Removed QA database")


if __name__ == "__main__":
    {"setup": setup, "compare": compare, "fixtures": fixtures,
     "check-fixtures": check_fixtures, "teardown": teardown}[sys.argv[1]]()
