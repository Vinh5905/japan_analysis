"""Exercise DAG scheduling/final status with mocked loader summaries.

Successful transformations are marked successful here; real SQL/tests are
covered separately by integration_dbt_airflow.py. No source batches are claimed.
"""

import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

os.environ.setdefault("AIRFLOW__COSMOS__ENABLE_TELEMETRY", "False")

log_path = Path("/opt/airflow/logs/dbt_airflow_qa/loader-cases.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
sys.stdout = log_path.open("w", buffering=1)
sys.stderr = sys.stdout

from airflow.models import DagBag
from airflow.utils import timezone

bag = DagBag("/opt/airflow/dags", include_examples=False)
assert not bag.import_errors, bag.import_errors
dag = bag.get_dag("suumo_load_to_warehouse")
module = sys.modules[dag.get_task("load_batches").python_callable.__module__]
cases = [
    ("no-batches", {"loaded_batch_ids": [], "results": []}, "success", "skipped"),
    (
        "success",
        {"loaded_batch_ids": [1], "results": [{"batch_id": 1, "status": "success"}]},
        "success",
        "success",
    ),
    (
        "all-failed",
        {"loaded_batch_ids": [], "results": [{"batch_id": 2, "status": "failed"}]},
        "failed",
        "skipped",
    ),
    (
        "mixed",
        {
            "loaded_batch_ids": [1],
            "results": [
                {"batch_id": 1, "status": "success"},
                {"batch_id": 2, "status": "failed"},
            ],
        },
        "failed",
        "success",
    ),
    (
        "loader-no-summary",
        RuntimeError("intentional QA loader failure before summary"),
        "failed",
        "upstream_failed",
    ),
]
reports = []
for name, summary, expected, prepared in cases:
    kwargs = (
        {"side_effect": summary}
        if isinstance(summary, Exception)
        else {"return_value": summary}
    )
    with patch.object(module, "load_pending_batches", **kwargs):
        mark_success = r"dbt\..*" if prepared == "success" else None
        run = dag.test(
            execution_date=timezone.utcnow(), mark_success_pattern=mark_success
        )
    states = {ti.task_id: ti.state for ti in run.get_task_instances()}
    assert run.state == expected, (name, run.state)
    assert states["prepare_transform"] == prepared, (name, states)
    if prepared == "skipped":
        assert all(
            state == "skipped"
            for task_id, state in states.items()
            if task_id.startswith("dbt.")
        )
    elif prepared == "success":
        assert all(
            state == "success"
            for task_id, state in states.items()
            if task_id.startswith("dbt.")
        )
    assert states["report_batch_failures"] == expected, (name, states)
    reports.append(
        {
            "case": name,
            "run_id": run.run_id,
            "state": run.state,
            "prepare_state": prepared,
        }
    )
output = Path("/opt/airflow/dbt/target/airflow/qa/loader-cases.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(reports, indent=2))
sys.__stdout__.write("QA PASS loader scheduling and final status: 5 cases\n")
