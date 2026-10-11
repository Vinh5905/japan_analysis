"""Compare local building migration against a saved pre-change baseline.

SELECT-only validation; materialization stays with dbt and audit DDL with loader.
"""

import argparse
import json
from pathlib import Path

from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)

BASELINE_QUERIES = {
    "facts": "select count(*), md5(string_agg(jsonb_build_array(task_id,record_origin,geography_key,observation_quality_key,parsed_date_key,parsed_at_utc,rent_jpy,management_fee_jpy,deposit_jpy,key_money_jpy,guarantee_deposit_jpy,depreciation_jpy,brokerage_fee_amount_jpy,other_initial_costs_total_jpy,insurance_jpy,parking_fee_jpy,exclusive_area_m2)::text, '' order by task_id)) from mart.fct_rental_price_observation",
    "price_history": "select count(*), md5(string_agg(jsonb_build_array(task_id,previous_task_id,previous_rent_jpy,next_task_id,rent_change_jpy,rent_change_pct,is_latest_known)::text,'' order by task_id)) from mart.rental_price_observations",
    "geography": "select count(*), md5(string_agg(to_jsonb(g)::text,'' order by geography_key)) from mart.dim_geography g",
    "listing_versions": "select count(*) from mart.dim_rental_listing",
    "latest": "select count(*) from analytics.rental_listing_latest",
    "raw": "select count(*), md5(string_agg(to_jsonb(r)::text,'' order by task_id)) from raw.suumo_parser_records r",
}


def fingerprints(connection):
    """Hash protected columns without surrogate listing keys that may change."""
    return {
        name: list(connection.execute(query).fetchone())
        for name, query in BASELINE_QUERIES.items()
    }


def verify(baseline_file, report_file):
    """Assert invariants and report name coverage, candidates and SCD count changes."""
    before = json.loads(Path(baseline_file).read_text())
    with postgres_connection(load_warehouse_postgres_config()) as connection:
        after = fingerprints(connection)
        for name in ("facts", "price_history", "geography", "latest", "raw"):
            assert before[name] == after[name], f"Protected invariant changed: {name}"
        count, named, rooms, candidates = connection.execute("""
            select count(*), count(*) filter (where building_name is not null),
                   count(*) filter (where room_number is not null),
                   count(distinct building_key) filter (where building_identity_status = 'named_candidate')
            from mart.rental_price_observations
        """).fetchone()
        operational, op_named = connection.execute("""
            select count(*), count(*) filter (where building_name is not null)
            from mart.rental_price_observations where record_origin = 'operational'
        """).fetchone()
        building_versions, building_identities, unresolved, conflicts = (
            connection.execute("""
            select count(*), count(distinct building_key),
                   count(distinct building_key) filter (where building_identity_status = 'unresolved_listing'),
                   (select count(*) from mart.fct_rental_price_observation where building_attributes_conflict)
            from mart.dim_building
        """).fetchone()
        )
        statuses = dict(
            connection.execute("""
            select building_name_parse_status, count(*) from raw.suumo_building_name_backfill
            group by building_name_parse_status
        """).fetchall()
        )
    result = {
        "protected_invariants": "unchanged",
        "before": before,
        "after": after,
        "listing_versions_delta": after["listing_versions"][0]
        - before["listing_versions"][0],
        "observations": count,
        "named_observations": named,
        "room_numbers": rooms,
        "name_coverage_pct": round(100 * named / count, 4),
        "operational_observations": operational,
        "operational_named": op_named,
        "named_building_candidates": candidates,
        "building_versions": building_versions,
        "building_identities": building_identities,
        "unresolved_listing_identities": unresolved,
        "conflicting_observations": conflicts,
        "backfill_statuses": statuses,
    }
    Path(report_file).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False))


def main():
    """Capture a future baseline or verify against the original local baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--report", default="building_coverage.json")
    args = parser.parse_args()
    if args.capture:
        with postgres_connection(load_warehouse_postgres_config()) as connection:
            result = fingerprints(connection)
        Path(args.baseline).write_text(json.dumps(result, indent=2))
    else:
        verify(args.baseline, args.report)


if __name__ == "__main__":
    main()
