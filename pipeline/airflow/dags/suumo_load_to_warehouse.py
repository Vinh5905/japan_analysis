from __future__ import annotations

import os
import subprocess
from datetime import datetime

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException

from loaders.suumo_batch_loader import load_pending_batches


def _batch_ids_from_conf(context) -> list[int] | None:
    """Return batch ids from dag_run.conf, or None for scheduled polling."""

    dag_run = context.get("dag_run")
    conf = dag_run.conf if dag_run and dag_run.conf else {}

    if "batch_id" in conf:
        return [int(conf["batch_id"])]

    batch_ids = conf.get("batch_ids")
    if batch_ids:
        return [int(batch_id) for batch_id in batch_ids]

    return None


def _run_dbt_command(args: list[str]) -> None:
    """Run one dbt command in the configured dbt project directory."""

    project_dir = os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt")
    profiles_dir = os.getenv("DBT_PROFILES_DIR", "/opt/airflow/dbt")
    command_env = {
        **os.environ,
        "DBT_PROFILES_DIR": profiles_dir,
    }
    subprocess.run(args, cwd=project_dir, env=command_env, check=True)


def _skip_when_no_loaded_batches(load_summary: dict) -> None:
    """Skip downstream dbt tasks when the loader found no successful batches."""

    if not load_summary.get("loaded_batch_ids"):
        raise AirflowSkipException("No warehouse batches were loaded")


@dag(
    dag_id="suumo_load_to_warehouse",
    start_date=datetime(2026, 1, 1),
    schedule=os.getenv("SUUMO_LOAD_DAG_SCHEDULE", "0 */3 * * *"),
    catchup=False,
    max_active_runs=1,
    tags=["suumo", "warehouse", "dbt"],
)
def suumo_load_to_warehouse():
    """Load source parser JSON batches into warehouse and run dbt models."""

    @task
    def load_batches(**context) -> dict:
        """Load one triggered batch or poll pending source batches."""

        batch_ids = _batch_ids_from_conf(context)
        limit = int(os.getenv("SUUMO_LOAD_BATCH_LIMIT", "20"))
        return load_pending_batches(batch_ids=batch_ids, limit=limit)

    @task
    def dbt_deps(load_summary: dict) -> dict:
        """Install dbt packages only when at least one batch was loaded."""

        _skip_when_no_loaded_batches(load_summary)
        _run_dbt_command(["dbt", "deps"])
        return load_summary

    @task
    def dbt_run(load_summary: dict) -> dict:
        """Run dbt models after new raw warehouse rows are available."""

        _skip_when_no_loaded_batches(load_summary)
        _run_dbt_command(["dbt", "run"])
        return load_summary

    @task
    def dbt_test(load_summary: dict) -> dict:
        """Run dbt tests after model refresh."""

        _skip_when_no_loaded_batches(load_summary)
        _run_dbt_command(["dbt", "test"])
        return load_summary

    load_summary = load_batches()
    deps_summary = dbt_deps(load_summary)
    run_summary = dbt_run(deps_summary)
    dbt_test(run_summary)


suumo_load_to_warehouse()
