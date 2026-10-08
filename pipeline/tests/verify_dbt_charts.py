"""Read-only integration checks for the rental BI boards using the real dct CLI.

Run inside the pipeline image after dbt-build. Render JSON checks chart execution
and column bindings; warehouse comparisons check population and filter semantics.
No test data is inserted and generated artifacts stay in a temporary directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile

import psycopg2


PROJECT = Path(os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt"))
BOARDS = (
    "rental_market_overview",
    "rental_pricing_opportunities",
    "rental_feature_pricing",
    "rental_station_access",
    "rental_data_quality",
)


def charts(board: dict):
    """Walk nested boards and yield charts, failing on any render error."""
    for item in board.get("items", []):
        if item.get("error"):
            raise AssertionError(item["error"])
        if item.get("type") == "chart":
            yield item
        elif item.get("type") == "board":
            yield from charts(item["board"])


def render(name: str, output: Path, **variables) -> dict:
    """Render a board without cache and verify its chart count and KPI grain."""
    command = [
        "dct", "render", f"charts/{name}.yml", "--format", "json",
        "--output", str(output), "--no-cache", "--project-dir", str(PROJECT),
    ]
    for key, value in variables.items():
        command.extend(["--var", f"{key}={value}"])
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise AssertionError(f"{name}: {result.stderr}\n{result.stdout}")
    payload = json.loads(output.read_text())
    rendered = {item["chart"]["id"]: item for item in charts(payload)}
    assert len(rendered) == 8, (name, list(rendered))
    for chart_id, item in rendered.items():
        chart = item["chart"]
        if chart["chart_type"] == "kpi":
            assert len(item["data"]) == 1, (name, chart_id, "KPI grain")
            assert chart["value"] in item["data"][0], (name, chart_id)
    print(f"PASS render {name} {variables or '(default)'}", flush=True)
    return rendered


def metric(rendered: dict, chart_id: str):
    """Read the bound value from a rendered single-row KPI."""
    item = rendered[chart_id]
    return item["data"][0][item["chart"]["value"]]


def main() -> None:
    """Compare rendered BI metrics with read-only warehouse queries."""
    connection = psycopg2.connect(
        host=os.environ["WAREHOUSE_POSTGRES_HOST"],
        port=os.environ["WAREHOUSE_POSTGRES_PORT"],
        dbname=os.environ["WAREHOUSE_DB"],
        user=os.environ["PIPELINE_POSTGRES_USER"],
        password=os.environ["PIPELINE_POSTGRES_PASSWORD"],
    )
    connection.set_session(readonly=True)
    try:
        with connection.cursor() as cursor, tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "board.json"
            defaults = {name: render(name, output) for name in BOARDS}
            cursor.execute("select count(*) from analytics.rental_listing_latest")
            total = cursor.fetchone()[0]
            market = defaults["rental_market_overview"]
            assert metric(market, "listing_count_kpi") == total
            assert metric(defaults["rental_data_quality"], "latest_listing_kpi") == total

            positions = defaults["rental_pricing_opportunities"]["price_position_chart"]["data"]
            if positions:
                assert abs(sum(float(row["listing_share_ratio"]) for row in positions) - 1) < 1e-9

            cursor.execute("""
                select layout_normalized, count(*)
                from analytics.rental_listing_latest
                where layout_normalized is not null
                group by 1 order by 2 desc, 1 limit 1
            """)
            layout = cursor.fetchone()
            if layout:
                filtered = render("rental_market_overview", output, layout=layout[0])
                assert metric(filtered, "listing_count_kpi") == layout[1]
                peer = render("rental_pricing_opportunities", output, layout=layout[0])
                cursor.execute("""
                    select count(*) from analytics.rental_listing_comparable_benchmark
                    where layout_normalized = %s and rent_position <> 'not_scored'
                """, (layout[0],))
                assert metric(peer, "scored_listings_kpi") == cursor.fetchone()[0]

            cursor.execute("""
                select locality, count(*) from analytics.rental_listing_latest
                where locality is not null group by 1 order by 2 desc, 1 limit 1
            """)
            locality = cursor.fetchone()
            if locality:
                filtered = render("rental_market_overview", output, locality=locality[0])
                assert metric(filtered, "listing_count_kpi") == locality[1]

            empty = render("rental_market_overview", output, locality="__bi_smoke_no_such_locality__")
            assert metric(empty, "listing_count_kpi") == 0
            assert metric(empty, "median_rent_kpi") is None

            stations = render("rental_station_access", output, max_travel_minutes=5)
            cursor.execute("""
                select count(distinct b.task_id)
                from mart.bridge_observation_station_access b
                join analytics.rental_listing_latest l on l.task_id = b.task_id
                join mart.dim_station_label d on d.station_label_key = b.station_label_key
                where b.parse_status = 'parsed' and b.total_travel_minutes <= 5
            """)
            assert metric(stations, "accessible_listings_kpi") == cursor.fetchone()[0]
            assert metric(stations, "accessible_listings_kpi") <= total

            for feature in ("floor_band", "direction", "structure", "building_type"):
                render("rental_feature_pricing", output, feature_name=feature)
            print("PASS population, filter, peer shares, empty state and station distinct-count checks", flush=True)
    finally:
        connection.rollback()
        connection.close()


if __name__ == "__main__":
    main()
