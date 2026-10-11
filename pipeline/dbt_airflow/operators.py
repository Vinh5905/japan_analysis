"""Thin Cosmos LOCAL operators with runtime selection and durable artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
from urllib.parse import quote

from airflow.exceptions import AirflowSkipException
from airflow.models import BaseOperator
from cosmos.operators.local import DbtRunLocalOperator, DbtTestLocalOperator

from dbt_airflow.manifest import assert_fresh


class SelectedTask:
    def configure_selection(self, dbt_node_ids, manifest_fingerprint):
        self.dbt_node_ids = dbt_node_ids
        self.manifest_fingerprint = manifest_fingerprint

    def execute(self, context):
        assert_fresh(
            Path(os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt")),
            self.manifest_fingerprint,
        )
        selection = context["ti"].xcom_pull(task_ids="prepare_transform")
        if not selection or not set(self.dbt_node_ids).intersection(
            selection["execute_ids"]
        ):
            raise AirflowSkipException(
                "Outside the selected dbt branch, or no successful batches"
            )
        self.log.info("dbt nodes: %s", self.dbt_node_ids)
        return super().execute(context)


class ArtifactTask(SelectedTask):
    def run_subprocess(self, command, env, cwd, **kwargs):
        # Copy before Cosmos removes its temporary directory, even on errors.
        ti = kwargs["context"]["ti"]
        destination = (
            Path(os.getenv("AIRFLOW_HOME", "/opt/airflow")) / "logs/dbt_artifacts"
        )
        destination = (
            destination
            / quote(ti.dag_id, safe="")
            / quote(ti.run_id, safe="")
            / quote(ti.task_id, safe="")
            / f"attempt={ti.try_number}"
        )
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "command.json").write_text(
            json.dumps({"nodes": self.dbt_node_ids, "command": command})
        )
        try:
            return super().run_subprocess(command, env, cwd, **kwargs)
        finally:
            for relative in (
                "target/run_results.json",
                "logs/dbt.log",
                "target/compiled",
                "target/run",
            ):
                source = Path(cwd) / relative
                target = destination / relative
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                elif source.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            self.log.info("dbt artifacts and compiled SQL: %s", destination)


# Airflow 2.10 wraps constructors/execute only when the concrete operator
# declares them; inheriting these methods from a plain mixin misses wrappers.
class SelectedDbtRunOperator(ArtifactTask, DbtRunLocalOperator):
    def __init__(self, *, dbt_node_ids, manifest_fingerprint, **kwargs):
        super().__init__(**kwargs)
        self.configure_selection(dbt_node_ids, manifest_fingerprint)

    def execute(self, context):
        return super().execute(context)


class SelectedDbtTestOperator(ArtifactTask, DbtTestLocalOperator):
    def __init__(self, *, dbt_node_ids, manifest_fingerprint, **kwargs):
        super().__init__(**kwargs)
        self.configure_selection(dbt_node_ids, manifest_fingerprint)

    def execute(self, context):
        return super().execute(context)


class ReusedRelationBaseOperator(BaseOperator):
    def execute(self, context):
        self.log.info("Using bootstrapped relation; no seed or source write")


class ReusedRelationOperator(SelectedTask, ReusedRelationBaseOperator):
    def __init__(self, *, dbt_node_ids, manifest_fingerprint, **kwargs):
        super().__init__(**kwargs)
        self.configure_selection(dbt_node_ids, manifest_fingerprint)

    def execute(self, context):
        return super().execute(context)
