"""Cosmos node converters and quality gates for the static manifest graph."""
from __future__ import annotations

import hashlib

from airflow.utils.task_group import TaskGroup
from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import DbtResourceType, ExecutionMode, InvocationMode, LoadMode, SourceRenderingBehavior, TestBehavior

from dbt_airflow.operators import ReusedRelationOperator, SelectedDbtRunOperator, SelectedDbtTestOperator
from dbt_airflow.selection import Selection


def test_selector(node):
    return "fqn:" + ".".join(node["fqn"])


class GraphBuilder:
    def __init__(self, manifest, project):
        self.graph = Selection(manifest)
        self.fingerprint = manifest["_airflow"]["fingerprint"]
        self.project = project
        self.runs = {}
        self.tests = {}
        self.units = {}
        self.entries = {}
        self.cross_group = None

    def operator_args(self, task_args, ids):
        return {**task_args, "dbt_node_ids": ids, "manifest_fingerprint": self.fingerprint,
                "trigger_rule": "none_failed", "retries": 0, "emit_datasets": False, "partial_parse": False}

    def make_test(self, *, ids, task_id, dag, task_group, task_args):
        nodes = {**self.graph.tests, **self.graph.units}
        operator = SelectedDbtTestOperator(
            task_id=task_id, dag=dag, task_group=task_group,
            select=[test_selector(nodes[uid]) for uid in ids], indirect_selection="empty",
            **self.operator_args(task_args, ids),
        )
        for uid in ids:
            self.tests[uid] = operator
        return operator

    def convert_resource(self, *, dag, task_group, node, task_args, **kwargs):
        uid = node.unique_id
        with TaskGroup(group_id=node.name, parent_group=task_group, dag=dag) as group:
            if uid in self.graph.models:
                run = SelectedDbtRunOperator(
                    task_id="run", select=self.graph.models[uid]["name"], dag=dag,
                    **self.operator_args(task_args, [uid]),
                )
                self.runs[uid] = run
            else:
                run = ReusedRelationOperator(
                    task_id="reuse", dag=dag, dbt_node_ids=[uid],
                    manifest_fingerprint=self.fingerprint, trigger_rule="none_failed",
                )
            self.entries[uid] = run
            own_tests = [tid for tid, test in self.graph.tests.items() if test["depends_on"]["nodes"] == [uid]]
            if own_tests:
                run >> self.make_test(ids=own_tests, task_id="test", dag=dag, task_group=group, task_args=task_args)
            for tid, test in self.graph.units.items():
                if uid in self.graph.models and test["model"] == self.graph.models[uid]["name"]:
                    unit = self.make_test(ids=[tid], task_id="unit_" + test["name"], dag=dag, task_group=group, task_args=task_args)
                    self.units[tid] = unit
                    unit >> run
                    self.entries[uid] = unit
        return group

    def convert_test(self, *, dag, task_group, task_id, task_args, **kwargs):
        # Cosmos 1.15.1's detached pass supplies the last iterated `node` to
        # converters, while task_id comes from the correct test metadata.
        # Resolve by that stable metadata ID rather than the stale node.
        candidates = [uid for uid, test in self.graph.tests.items()
                      if len(test["depends_on"]["nodes"]) > 1
                      and test["name"] + "_test" == task_id]
        if len(candidates) != 1:
            raise RuntimeError(f"Cannot resolve Cosmos detached test {task_id}")
        tid = candidates[0]
        if self.cross_group is None:
            self.cross_group = TaskGroup(group_id="cross_model_tests", parent_group=dag.task_group.children["dbt"], dag=dag)
        # Stable hash, rather than a parse-time counter, for generated names.
        task_id = self.graph.tests[tid]["name"][:170] + "_" + hashlib.sha256(tid.encode()).hexdigest()[:10]
        return self.make_test(ids=[tid], task_id=task_id, dag=dag, task_group=self.cross_group, task_args=task_args)

    def build(self, dag):
        profile = ProfileConfig(profile_name="japan_analysis", target_name="dev", profiles_yml_filepath=self.project / "profiles.yml")
        arguments = {
            "emit_datasets": False, "partial_parse": False,
            "dbt_cmd_flags": ["--threads", "1"],
            "dbt_cmd_global_flags": ["--warn-error-options", '{"error": ["NoNodesForSelectionCriteria"]}'],
        }
        group = DbtTaskGroup(
            group_id="dbt", dag=dag,
            project_config=ProjectConfig(dbt_project_path=self.project, manifest_path=self.project / "target/airflow/manifest.json", install_dbt_deps=False, partial_parse=False),
            profile_config=profile,
            execution_config=ExecutionConfig(execution_mode=ExecutionMode.LOCAL, invocation_mode=InvocationMode.SUBPROCESS,
                                             dbt_executable_path="/opt/airflow/dbt_venv/bin/dbt"),
            render_config=RenderConfig(
                load_method=LoadMode.DBT_MANIFEST, test_behavior=TestBehavior.AFTER_EACH,
                should_detach_multiple_parents_tests=True, group_nodes_by_folder=True,
                source_rendering_behavior=SourceRenderingBehavior.ALL,
                exclude=["resource_type:unit_test", "resource_type:exposure"], node_conversion_by_task_group=True,
                node_converters={DbtResourceType.MODEL: self.convert_resource,
                                 DbtResourceType.SEED: self.convert_resource,
                                 DbtResourceType.SOURCE: self.convert_resource,
                                 DbtResourceType.TEST: self.convert_test},
            ), operator_args=arguments,
        )
        # Cosmos deep-copies RenderConfig (including bound converter methods).
        # Recover the resulting operators from the DAG rather than relying on
        # mutations of this builder across that copied configuration.
        self.tests = {uid: operator for operator in dag.tasks
                      if isinstance(operator, SelectedDbtTestOperator) for uid in operator.dbt_node_ids}
        self.runs = {uid: operator for operator in dag.tasks
                     if isinstance(operator, SelectedDbtRunOperator) for uid in operator.dbt_node_ids}
        self.entries = {uid: operator for operator in dag.tasks
                        if isinstance(operator, (SelectedDbtRunOperator, ReusedRelationOperator))
                        for uid in operator.dbt_node_ids}
        for tid, unit in self.graph.units.items():
            self.entries[self.graph.names[unit["model"]]] = self.tests[tid]
        # AFTER_EACH does not render the three self-contained tests with no refs.
        with TaskGroup(group_id="standalone_tests", parent_group=group, dag=dag) as standalone:
            for tid, test in self.graph.tests.items():
                if not test["depends_on"]["nodes"]:
                    self.make_test(ids=[tid], task_id=test["name"], dag=dag, task_group=standalone,
                                   task_args={**arguments, "project_dir": str(self.project), "profile_config": profile,
                                              "install_deps": False,
                                              "dbt_executable_path": "/opt/airflow/dbt_venv/bin/dbt",
                                              "invocation_mode": InvocationMode.SUBPROCESS})
        # Use the original relation graph when adding gates, to avoid cycles.
        for tid, test in self.graph.tests.items():
            parents = set(test["depends_on"]["nodes"])
            if len(parents) > 1:
                for mid in self.graph.models:
                    if parents.issubset(self.graph.ancestors(mid)):
                        self.tests[tid] >> self.entries[mid]
        expected = set(self.graph.tests) | set(self.graph.units)
        if set(self.tests) != expected:
            raise RuntimeError(f"Unrendered dbt tests: {expected - set(self.tests)}")
        return group

    def gate_geocoding(self, enrichment):
        """Insert HTTP enrichment at the address/cache boundary, without splitting Cosmos.

        Use only address-side gates. A test also reading the coordinate cache
        would create a cycle if it became a prerequisite of the cache writer.
        """
        observations = self.graph.names['int_suumo__mart_observations']
        cache = next(uid for uid, node in self.graph.nodes.items()
                     if node['resource_type'] == 'source'
                     and node['source_name'] == 'warehouse_raw'
                     and node['name'] == 'suumo_address_geocodes')
        self.runs[observations] >> enrichment
        address_side = self.graph.ancestors(observations) | {observations}
        for tid, test in self.graph.tests.items():
            parents = set(test['depends_on']['nodes'])
            if ((parents and parents.issubset(address_side))
                    or test['name'] == 'assert_suumo_geocode_address_query'):
                self.tests[tid] >> enrichment
        enrichment >> self.entries[cache]
