"""SELECT-only validation and coverage export against pre-enrichment baseline."""

import argparse
import csv
import json
from pathlib import Path

from psycopg import sql
from psycopg.rows import dict_row
from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)

ROOT = Path("/opt/airflow/dbt/target/building_locations")


def main(capture_baseline=False):
    ROOT.mkdir(parents=True, exist_ok=True)
    baseline = (
        {} if capture_baseline else json.loads((ROOT / "baseline.json").read_text())
    )
    queries = {
        "fact": "select count(*), md5(string_agg(to_jsonb(f)::text,'' order by task_id)) from mart.fct_rental_price_observation f",
        "listing": "select count(*), md5(string_agg(to_jsonb(l)::text,'' order by listing_version_key)) from mart.dim_rental_listing l",
        "geography": "select count(*), md5(string_agg(to_jsonb(g)::text,'' order by geography_key)) from mart.dim_geography g",
        "raw": "select count(*), md5(string_agg(to_jsonb(r)::text,'' order by task_id)) from raw.suumo_parser_records r",
        "prices": "select count(*), md5(string_agg(jsonb_build_array(task_id,previous_task_id,previous_rent_jpy,next_task_id,rent_change_jpy,rent_change_pct,is_latest_known)::text,'' order by task_id)) from mart.rental_price_observations",
    }
    with postgres_connection(load_warehouse_postgres_config()) as conn:
        if capture_baseline:
            enrichment_columns = (
                "building_full_address_raw",
                "building_full_address",
                "postal_code",
                "address_block",
                "address_house_number",
                "latitude",
                "longitude",
                "coordinate_level",
                "geocode_status",
                "geocode_provider",
                "geocode_matched_address",
                "geocode_match_method",
                "geocoded_at",
                "google_place_id",
                "google_maps_url",
            )
            baseline["building_columns"] = [
                row[0]
                for row in conn.execute(
                    "select column_name from information_schema.columns where table_schema='mart' "
                    "and table_name='dim_building' and not (column_name=any(%s)) order by ordinal_position",
                    (list(enrichment_columns),),
                ).fetchall()
            ]
            assert baseline["building_columns"], (
                "Build the existing building mart before capturing baseline"
            )
        after = {
            key: list(conn.execute(query).fetchone()) for key, query in queries.items()
        }
        query = sql.SQL(
            "select count(*), md5(string_agg(to_jsonb(b)::text,'' order by building_version_key)) from (select {} from mart.dim_building) b"
        ).format(sql.SQL(",").join(map(sql.Identifier, baseline["building_columns"])))
        after["building"] = list(conn.execute(query).fetchone())
        if capture_baseline:
            baseline.update(after)
            (ROOT / "baseline.json").write_text(json.dumps(baseline, indent=2))
            print("Captured baseline.json; no warehouse writes or HTTP requests")
            return
        for key in after:
            assert baseline[key] == after[key], f"Protected data changed: {key}"
        total, matched, named = conn.execute(
            "select count(*), count(*) filter(where geocode_status='matched'), count(*) filter(where building_identity_status='named_candidate') from mart.rental_price_observations"
        ).fetchone()
        eligible, matched_buildings = conn.execute(
            "select count(*), count(*) filter(where c.status='matched') from intermediate.int_suumo__building_lookup_candidates q left join staging.stg_suumo__building_locations c using(building_key)"
        ).fetchone()
        statuses = dict(
            conn.execute(
                "select geocode_status,count(*) from mart.rental_price_observations group by geocode_status"
            ).fetchall()
        )
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "select q.building_key,q.building_name_normalized,q.building_address_query,c.status,c.error_message from intermediate.int_suumo__building_lookup_candidates q left join staging.stg_suumo__building_locations c using(building_key) where c.status is distinct from 'matched'"
            )
            unmatched = list(cursor.fetchall())
            cursor.execute(
                "select task_id,suumo_property_code,building_key,building_name,building_identity_status,room_number,building_full_address_raw,building_full_address,postal_code,address_block,address_house_number,latitude,longitude,coordinate_level,geocode_status,geocode_match_method,google_place_id,google_maps_url,geocoded_at from mart.rental_price_observations where building_identity_status='named_candidate' order by task_id limit 10"
            )
            sample = list(cursor.fetchall())
            cursor.execute(
                "select building_key,building_name,building_full_address,latitude,longitude,coordinate_level,geocode_status,google_place_id,google_maps_url from mart.dim_building where building_identity_status='named_candidate' and is_current order by building_key limit 10"
            )
            building_sample = list(cursor.fetchall())
            cursor.execute(
                "select task_id,suumo_property_code,building_key,building_name,building_identity_status,geocode_status from mart.rental_price_observations where geocode_status<>'matched' order by task_id"
            )
            with (ROOT / "unmatched_observations.csv").open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=[column.name for column in cursor.description]
                )
                writer.writeheader()
                writer.writerows(cursor)
        coverage = {
            "eligible_buildings": eligible,
            "matched_buildings": matched_buildings,
            "building_coverage_pct": round(100 * matched_buildings / eligible, 4)
            if eligible
            else None,
            "observations": total,
            "matched_observations": matched,
            "named_observations": named,
            "observation_coverage_pct": round(100 * matched / total, 4)
            if total
            else None,
            "named_observation_coverage_pct": round(100 * matched / named, 4)
            if named
            else None,
            "statuses": statuses,
            "unmatched_candidates": unmatched,
        }
    report = {
        "protected_invariants": "unchanged",
        "before": baseline,
        "after": after,
        "listing_versions_delta": 0,
        "building_versions_delta": 0,
        "coverage": coverage,
        "sample": sample,
        "building_sample": building_sample,
    }
    (ROOT / "coverage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str)
    )
    lines = [
        "# Kết quả building lookup local",
        "",
        f"- Địa chỉ/tọa độ matched: {matched_buildings}/{eligible} ứng viên đủ đầu vào.",
        f"- Observation có tọa độ: {matched}/{total} ({coverage['observation_coverage_pct']}%).",
        "- Các khóa, giá/diện tích, số observation và phiên bản SCD2 giữ nguyên.",
        "- building_poi là điểm provider; chưa xác minh độc lập mái tòa.",
        "",
        "| Tên tòa chuẩn hóa | Địa chỉ chi tiết | Latitude | Longitude | Trạng thái |",
        "|---|---|---:|---:|---|",
    ]
    for row in building_sample:
        lat = f"{row['latitude']:.7f}" if row["latitude"] is not None else "NULL"
        lon = f"{row['longitude']:.7f}" if row["longitude"] is not None else "NULL"
        lines.append(
            f"| {row['building_name']} | {row['building_full_address'] or 'NULL'} | {lat} | {lon} | {row['geocode_status']} |"
        )
    lines.extend(
        [
            "",
            "Chi tiết audit/Place ID/URL và mẫu observation: coverage.json.",
            "Các observation chưa matched: unmatched_observations.csv.",
            "Tên NULL không được fallback sang điểm chōme.",
        ]
    )
    (ROOT / "report.md").write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {"protected_invariants": "unchanged", "coverage": coverage},
            ensure_ascii=False,
            default=str,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-baseline",
        action="store_true",
        help="Capture before deployment; SELECT-only",
    )
    main(capture_baseline=parser.parse_args().capture_baseline)
