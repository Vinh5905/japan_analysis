"""SELECT-only MLIT coverage, protected baseline and additive view verification."""

import csv
import json
from pathlib import Path
from psycopg import sql
from psycopg.rows import dict_row
from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)
from tests import verify_building_locations_warehouse as baseline

ROOT = Path("/opt/airflow/dbt/target/mlit_zoning")


def main():
    # Reuse the original SELECT-only fingerprints; retain its full result separately.
    baseline.ROOT = ROOT
    baseline.main()
    prior = json.loads((ROOT / "coverage.json").read_text())
    with (
        postgres_connection(load_warehouse_postgres_config()) as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        cur.execute(
            "select r.*,d.fiscal_year,d.source_as_of_date,d.source_modified_date,d.zip_sha256,d.feature_count from enrichment.zoning_publication_pointer p join enrichment.zoning_runs r using(run_id) join raw.mlit_datasets d using(dataset_key) where p.city_code='27100'"
        )
        publication = cur.fetchone()
        assert publication, "No active publication"
        cur.execute(
            """select i.building_key,i.building_name,i.address_query,i.latitude,i.longitude,m.*
          from enrichment.zoning_run_inputs i join intermediate.int_mlit__published_results m using(run_id,building_key)
          where i.run_id=%s order by i.building_key""",
            (publication["run_id"],),
        )
        buildings = list(cur.fetchall())
        cur.execute(
            "select zoning_status,count(*) as n from mart.rental_price_observations_with_zoning group by zoning_status order by zoning_status"
        )
        statuses = {x["zoning_status"]: x["n"] for x in cur.fetchall()}
        cur.execute(
            "select count(*) as n from mart.rental_price_observations_with_zoning"
        )
        total = cur.fetchone()["n"]
        matched = sum(b["zoning_status"] == "matched" for b in buildings)
        matched_obs = statuses.get("matched", 0)
        for schema, base in [
            ("mart", "rental_price_observations"),
            ("mart", "rental_prices_latest_known"),
            ("analytics", "rental_listing_latest"),
        ]:
            # Compare every original business column, including prices/area/keys/coordinates.
            cur.execute(
                "select column_name from information_schema.columns where table_schema=%s and table_name=%s order by ordinal_position",
                (schema, base),
            )
            cols = [x["column_name"] for x in cur.fetchall()]
            expected = conn.execute(
                sql.SQL(
                    "select count(*),md5(string_agg(to_jsonb(x)::text,'' order by task_id)) from {} x"
                ).format(sql.Identifier(schema, base))
            ).fetchone()
            actual = conn.execute(
                sql.SQL(
                    "select count(*),md5(string_agg(to_jsonb(x)::text,'' order by task_id)) from (select {} from {}) x"
                ).format(
                    sql.SQL(",").join(map(sql.Identifier, cols)),
                    sql.Identifier(schema, base + "_with_zoning"),
                )
            ).fetchone()
            assert expected == actual, f"Original columns/grain changed in {base}"
        cur.execute(
            "select * from mart.rental_price_observations_with_zoning where zoning_status<>'matched' order by task_id"
        )
        with (ROOT / "unmatched_observations.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=[c.name for c in cur.description]
            )
            writer.writeheader()
            writer.writerows(cur)
        cur.execute(
            "select task_id,building_key,building_name,zoning_status,zoning_code,zoning_name,far_pct,bcr_pct,building_zoning_version_key,zoning_publication_run_id,zoning_source_as_of_date,zoning_boundary_distance_m from mart.rental_price_observations_with_zoning where building_identity_status='named_candidate' order by task_id"
        )
        samples = list(cur.fetchall())
        for filename, rows in [
            ("building_sample.csv", buildings),
            ("observation_sample.csv", samples),
        ]:
            if rows:
                with (ROOT / filename).open("w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
    coverage = {
        "candidate_buildings": len(buildings),
        "matched_buildings": matched,
        "building_coverage_pct": 100 * matched / len(buildings) if buildings else None,
        "observations": total,
        "matched_observations": matched_obs,
        "observation_coverage_pct": 100 * matched_obs / total if total else None,
        "statuses": statuses,
    }
    result = {
        "protected_invariants": "unchanged",
        "baseline": prior["before"],
        "after": prior["after"],
        "listing_versions_delta": 0,
        "building_versions_delta": 0,
        "publication": publication,
        "coverage": coverage,
        "building_sample": buildings,
        "observation_sample": samples,
    }
    (ROOT / "coverage.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str)
    )
    lines = [
        "# MLIT zoning: kết quả local",
        "",
        "- Baseline observation, giá/diện tích, geography và SCD2 building/listing: không đổi.",
        "- Ba view mới giữ nguyên tất cả cột và grain của view gốc.",
        f"- Polygon Osaka-shi: {publication['feature_count']}; fiscal year {publication['fiscal_year']}; mốc dữ liệu thành phố {publication['source_as_of_date']}.",
        f"- Matched theo tòa: {matched}/{len(buildings)}.",
        f"- Matched theo observation: {matched_obs}/{total} ({coverage['observation_coverage_pct']:.4f}%).",
        "- Tọa độ là building POI của provider; FAR/BCR là chỉ tiêu chỉ định trên polygon quy hoạch, chưa phải giới hạn pháp lý riêng của lô đất.",
        "- Đây là quy hoạch tại publication đang dùng, không phải quy hoạch lịch sử vào ngày observation.",
        "",
        "| Tòa | Trạng thái | 用途地域 | FAR | BCR | Cách ranh (m) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for b in buildings:
        lines.append(
            f"| {b['building_name']} | {b['zoning_status']} | {b['zoning_name'] or 'NULL'} | {b['far_pct'] if b['far_pct'] is not None else 'NULL'} | {b['bcr_pct'] if b['bcr_pct'] is not None else 'NULL'} | {b['boundary_distance_m']:.3f} |"
        )
    lines.extend(
        [
            "",
            "WESTGATE: giữ candidate polygon trong coverage.json; output chính NULL do dưới ngưỡng 10 m.",
            "Danh sách toàn bộ observation chưa matched: unmatched_observations.csv.",
            "Mẫu tòa và observation: building_sample.csv, observation_sample.csv.",
            "Export publication cố định cùng manifest/task/input: thư mục ds_export.",
            "Các kiểm thử và thông tin image/package: verification.json, postgis_image.json.",
        ]
    )
    (ROOT / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(coverage, ensure_ascii=False))


if __name__ == "__main__":
    main()
