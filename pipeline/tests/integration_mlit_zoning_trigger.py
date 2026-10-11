"""Explicit local scheduler integration; SUUMO must be paused, MLIT unpaused.

Run in the Airflow image. Rebuilds only zoning input/output, uses the existing
MLIT source, and asserts the child run really succeeded (not skipped).
"""

import json
from pathlib import Path
from airflow.models import DagBag, DagModel, DagRun
from airflow.utils.session import create_session


def main():
    with create_session() as session:
        assert (
            session.query(DagModel)
            .filter_by(dag_id="suumo_load_to_warehouse")
            .one()
            .is_paused
        )
        assert (
            not session.query(DagModel)
            .filter_by(dag_id="mlit_zoning_refresh")
            .one()
            .is_paused
        )
    dag = DagBag("/opt/airflow/dags", include_examples=False).get_dag(
        "suumo_load_to_warehouse"
    )
    run = dag.test(run_conf={"mode": "dbt_only", "model": "int_suumo__zoning_inputs"})
    assert run.state == "success", run.state
    tasks = {t.task_id: t for t in run.get_task_instances()}
    assert tasks["prepare_zoning_refresh"].state == "success"
    trigger = tasks["refresh_zoning_publication"]
    assert trigger.state == "success", trigger.state
    child_id = trigger.xcom_pull(task_ids=trigger.task_id, key="trigger_run_id")
    with create_session() as session:
        child = (
            session.query(DagRun)
            .filter_by(dag_id="mlit_zoning_refresh", run_id=child_id)
            .one()
        )
        assert child.state == "success", child.state
        assert child.conf == {"mode": "reuse_source"}, child.conf
        evidence = {
            "parent_run_id": run.run_id,
            "parent_state": run.state,
            "trigger_state": trigger.state,
            "child_run_id": child.run_id,
            "child_state": child.state,
            "child_conf": child.conf,
        }
    Path("/opt/airflow/dbt/target/mlit_zoning/trigger_evidence.json").write_text(
        json.dumps(evidence, indent=2)
    )
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
