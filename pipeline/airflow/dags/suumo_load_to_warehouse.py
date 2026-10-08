from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task
from airflow.exceptions import AirflowSkipException
from airflow.models.param import Param
from airflow.utils.trigger_rule import TriggerRule

from dbt_airflow.graph import GraphBuilder
from dbt_airflow.manifest import assert_fresh, load_manifest
from dbt_airflow.selection import Selection, batch_failures, execution_failures
from loaders.suumo_batch_loader import load_pending_batches, load_warehouse_postgres_config, postgres_connection

PROJECT = Path(os.getenv("DBT_PROJECT_DIR", "/opt/airflow/dbt"))
MANIFEST = load_manifest(PROJECT)
GRAPH = Selection(MANIFEST)


def _conf(context):
    run = context.get("dag_run")
    return {**context.get("params", {}), **((run.conf or {}) if run else {})}


def _batch_ids_from_conf(conf):
    if "batch_id" in conf:
        return [int(conf["batch_id"])]
    if conf.get("batch_ids"):
        return [int(batch_id) for batch_id in conf["batch_ids"]]
    return None


@dag(
    dag_id="suumo_load_to_warehouse", start_date=datetime(2026, 1, 1),
    schedule=os.getenv("SUUMO_LOAD_DAG_SCHEDULE", "0 */3 * * *"), catchup=False,
    max_active_runs=1, max_active_tasks=int(os.getenv("SUUMO_DBT_CONCURRENCY", "4")),
    default_args={"retries": 0}, tags=["suumo", "warehouse", "dbt"],
    params={"mode": Param("load_and_transform", enum=["load_and_transform", "dbt_only"]),
            "model": Param(None, type=["null", "string"], description="Exact enabled model name; dbt_only only")},
)
def suumo_load_to_warehouse():
    @task
    def load_batches(**context):
        conf = _conf(context)
        mode, _ = GRAPH.resolve(conf)
        assert_fresh(PROJECT, MANIFEST["_airflow"]["fingerprint"])
        if mode == "dbt_only":
            return {"loaded_batch_ids": [], "results": []}
        return load_pending_batches(batch_ids=_batch_ids_from_conf(conf), limit=int(os.getenv("SUUMO_LOAD_BATCH_LIMIT", "20")))

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def prepare_transform(**context):
        mode, selected = GRAPH.resolve(_conf(context))
        assert_fresh(PROJECT, MANIFEST["_airflow"]["fingerprint"])
        summary = context["ti"].xcom_pull(task_ids="load_batches")
        if mode != "dbt_only" and not (summary or {}).get("loaded_batch_ids"):
            raise AirflowSkipException("No successful warehouse batches were loaded")
        missing = []
        with postgres_connection(load_warehouse_postgres_config()) as connection:
            with connection.cursor() as cursor:
                for uid in sorted(GRAPH.reused_relations(selected)):
                    relation = GRAPH.nodes[uid]["relation_name"]
                    cursor.execute("select to_regclass(%s)", (relation,))
                    if cursor.fetchone()[0] is None:
                        missing.append(f"{uid}: {relation}")
        if missing:
            raise RuntimeError("Missing reused upstream relations; bootstrap/build upstream first: " + "; ".join(missing))
        tests = {uid for uid in GRAPH.tests if GRAPH.test_is_selected(uid, selected)}
        units = {uid for uid, node in GRAPH.units.items() if GRAPH.names[node["model"]] in selected}
        reused = {uid for uid, node in GRAPH.nodes.items() if node["resource_type"] in {"source", "seed"}}
        return {"execute_ids": sorted(selected | tests | units | reused)}

    @task(trigger_rule=TriggerRule.ALL_DONE)
    def report_batch_failures(**context):
        summary = context["ti"].xcom_pull(task_ids="load_batches")
        failed_batches = batch_failures(summary)
        failed_tasks = execution_failures(context["dag_run"].get_task_instances())
        if failed_batches or failed_tasks:
            raise RuntimeError(f"Failed batch IDs: {failed_batches}; failed/upstream_failed tasks: {failed_tasks}")

    loader = load_batches()
    prepare = prepare_transform()
    loader >> prepare
    builder = GraphBuilder(MANIFEST, PROJECT)
    transform = builder.build(prepare.operator.dag)
    prepare >> transform
    report = report_batch_failures()
    # All tasks must be terminal, including a loader that returned no summary.
    for operator in list(report.operator.dag.tasks):
        if operator is not report.operator:
            operator >> report


suumo_load_to_warehouse()
