"""Single writer for MLIT evaluation models; publication is an atomic pointer."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.models.param import Param

from dbt_airflow.manifest import assert_fresh, load_manifest
from loaders.mlit_zoning_loader import refresh_source
from loaders.mlit_zoning_publication import prepare_run, check_run, publish_run

PROJECT = Path(os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt"))
MANIFEST = load_manifest(PROJECT)


def dbt_command(command, run, selection):
    run_id = run["run_id"]
    artifact = PROJECT / "target" / "mlit_runs" / run_id
    artifact.mkdir(parents=True, exist_ok=True)
    variables = json.dumps(
        {"mlit_run_id": run_id, "mlit_dataset_key": run["dataset_key"]}
    )
    cmd = [
        "/opt/airflow/dbt_venv/bin/dbt",
        command,
        "--project-dir",
        str(PROJECT),
        "--profiles-dir",
        str(PROJECT),
        "--target-path",
        str(artifact),
        "--log-path",
        str(artifact / "logs"),
        "--select",
        selection,
        "--vars",
        variables,
        "--threads",
        "1",
        "--no-partial-parse",
    ]
    # Stream useful progress to Airflow log; do not place artifacts/responses in XCom.
    subprocess.run(cmd, check=True)
    if command == "build":
        result = json.loads((artifact / "run_results.json").read_text())
        if any(
            x["status"] not in ("success", "pass", "warn") for x in result["results"]
        ):
            raise RuntimeError("MLIT build/tests failed")


@dag(
    dag_id="mlit_zoning_refresh",
    start_date=pendulum.datetime(2026, 1, 1, tz="Asia/Tokyo"),
    schedule=os.getenv("MLIT_ZONING_SCHEDULE", "0 3 * * 1"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    default_args={"retries": 0},
    tags=["mlit", "zoning", "warehouse"],
    params={"mode": Param("refresh_source", enum=["refresh_source", "reuse_source"])},
)
def mlit_zoning_refresh():
    @task
    def source_candidate(**context):
        assert_fresh(PROJECT, MANIFEST["_airflow"]["fingerprint"])
        conf = {**context["params"], **(context["dag_run"].conf or {})}
        mode = conf.get("mode", "refresh_source")
        if mode == "refresh_source":
            return refresh_source()
        if mode == "reuse_source":
            return {"dataset_key": None, "reused": True}
        raise ValueError("Unknown MLIT mode")

    @task
    def validate_polygons(source):
        # A temporary run context is sufficient for scope-specific polygon tests.
        if source["dataset_key"] is None:
            from loaders.mlit_zoning_publication import connection

            with connection() as conn:
                row = conn.execute(
                    """
                    select dataset_key
                    from raw.mlit_datasets
                    where city_code = '27100'
                    order by last_checked_at desc, dataset_key
                    limit 1
                    """
                ).fetchone()
                if not row:
                    raise RuntimeError("Refresh MLIT source before reuse_source")
                source = {**source, "dataset_key": row[0]}
        dbt_command(
            "build",
            {
                "run_id": "validate_" + source["dataset_key"],
                "dataset_key": source["dataset_key"],
            },
            "+int_mlit__polygon_states",
        )
        return source

    @task
    def snapshot_inputs(source):
        return prepare_run(source["dataset_key"])

    @task
    def spatial_matching(run):
        dbt_command("build", run, "tag:mlit_zoning_core")
        return {"run_id": run["run_id"], "dataset_key": run["dataset_key"]}

    @task
    def quality_and_diff(run):
        dbt_command("test", run, "tag:mlit_zoning_output")
        result = check_run(run["run_id"])
        return {"run_id": run["run_id"], "regression_count": len(result["regressions"])}

    @task
    def publish_candidate(review):
        # A blocked candidate is a successful audited check, not a partial publication.
        result = publish_run(review["run_id"])
        return result

    publish_candidate(
        quality_and_diff(
            spatial_matching(snapshot_inputs(validate_polygons(source_candidate())))
        )
    )


mlit_zoning_refresh()
