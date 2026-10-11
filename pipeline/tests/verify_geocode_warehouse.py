"""Capture/compare business rows before and after enrichment; no fixture writes."""

import argparse
import json
from pathlib import Path

from psycopg import sql
from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)

TABLES = [
    ("raw", "suumo_parser_records"),
    ("mart", "fct_rental_price_observation"),
    ("mart", "dim_rental_listing"),
    ("mart", "dim_geography"),
    ("mart", "bridge_observation_station_access"),
    ("mart", "rental_price_observations"),
    ("mart", "rental_prices_latest_known"),
    ("analytics", "rental_listing_latest"),
]


def fingerprints(reference=None):
    result = {}
    with postgres_connection(load_warehouse_postgres_config()) as conn:
        for schema, table in TABLES:
            name = schema + "." + table
            columns = (
                reference[name]["columns"]
                if reference
                else [
                    row[0]
                    for row in conn.execute(
                        "select column_name from information_schema.columns where table_schema=%s and table_name=%s order by ordinal_position",
                        (schema, table),
                    ).fetchall()
                ]
            )
            if not columns:
                raise RuntimeError("Missing relation " + name)
            query = sql.SQL(
                "select count(*), md5(coalesce(string_agg(payload, '' order by payload), '')) "
                "from (select to_jsonb(r)::text as payload from (select {} from {}) r) s"
            ).format(
                sql.SQL(", ").join(map(sql.Identifier, columns)),
                sql.Identifier(schema, table),
            )
            count, digest = conn.execute(query).fetchone()
            result[name] = {"columns": columns, "count": count, "digest": digest}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument(
        "--path",
        default="/opt/airflow/dbt/target/airflow/geocode_business_baseline.json",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if args.capture:
        path.parent.mkdir(parents=True, exist_ok=True)
        result = fingerprints()
        path.write_text(json.dumps(result, indent=2))
        print(json.dumps({name: row["count"] for name, row in result.items()}))
    else:
        before = json.loads(path.read_text())
        after = fingerprints(before)
        if before != after:
            raise AssertionError(
                {
                    name: {"before": before[name], "after": after[name]}
                    for name in before
                    if before[name] != after[name]
                }
            )
        print("Business rows/keys unchanged in " + str(len(before)) + " relations")
        with postgres_connection(load_warehouse_postgres_config()) as conn:
            rows = conn.execute(
                "select geocode_status, count(*) from mart.dim_geography group by 1 order by 1"
            ).fetchall()
            coverage = conn.execute(
                "select count(*), count(latitude) from analytics.rental_listing_latest"
            ).fetchone()
            print(
                json.dumps(
                    {
                        "geographies": rows,
                        "latest_listings": coverage[0],
                        "latest_with_coordinates": coverage[1],
                    }
                )
            )


if __name__ == "__main__":
    main()
