import unittest
from pathlib import Path
from types import SimpleNamespace
from airflow.models import DagBag
from airflow.exceptions import AirflowSkipException
from airflow.utils.dag_cycle_tester import check_cycle
from dbt_airflow.selection import Selection
from dbt_airflow.manifest import load_manifest
from dbt_airflow.operators import SelectedDbtRunOperator, ReusedRelationOperator


class ZoningDagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bag = DagBag("/opt/airflow/dags", include_examples=False)
        cls.suumo = cls.bag.get_dag("suumo_load_to_warehouse")
        cls.mlit = cls.bag.get_dag("mlit_zoning_refresh")
        cls.graph = Selection(load_manifest(Path("/opt/airflow/dbt")))

    def test_no_cycle_single_writer_and_schedule(self):
        self.assertFalse(self.bag.import_errors)
        check_cycle(self.suumo)
        check_cycle(self.mlit)
        self.assertEqual(self.mlit.max_active_runs, 1)
        self.assertFalse(self.mlit.catchup)
        self.assertEqual(str(self.mlit.timezone), "Asia/Tokyo")
        self.assertEqual(self.mlit.schedule_interval, "0 3 * * 1")
        core = self.graph.external_models
        for t in self.suumo.tasks:
            if isinstance(t, SelectedDbtRunOperator):
                self.assertFalse(set(t.dbt_node_ids) & core)
        reused = {
            uid
            for t in self.suumo.tasks
            if isinstance(t, ReusedRelationOperator)
            for uid in t.dbt_node_ids
        }
        self.assertTrue(core <= reused)

    def test_selection_input_gates_and_reuse(self):
        trigger = self.suumo.get_task("refresh_zoning_publication")
        self.assertEqual(trigger.conf, {"mode": "reuse_source"})
        self.assertTrue(trigger.wait_for_completion)
        # Reused/skipped dbt tests must not skip a selected lookup. The chooser
        # waits for quality gates with NONE_FAILED; its own skip still prevents
        # analytics-only branches from triggering another DAG.
        choice = self.suumo.get_task("prepare_zoning_refresh")
        self.assertEqual(str(choice.trigger_rule), "none_failed")
        self.assertEqual(str(trigger.trigger_rule), "all_success")
        self.assertEqual(trigger.upstream_task_ids, {choice.task_id})
        by_uid = {
            uid: t
            for t in self.suumo.tasks
            if isinstance(t, SelectedDbtRunOperator)
            for uid in t.dbt_node_ids
        }
        ancestors = {t.task_id for t in trigger.get_flat_relatives(upstream=True)}
        self.assertIn(
            by_uid[self.graph.names["int_suumo__zoning_inputs"]].task_id, ancestors
        )
        output = by_uid[self.graph.names["rental_price_observations_with_zoning"]]
        self.assertIn(
            trigger.task_id,
            {t.task_id for t in output.get_flat_relatives(upstream=True)},
        )
        chooser = self.suumo.get_task("prepare_zoning_refresh").python_callable
        for root in ("rental_listing_latest", "rental_listing_latest_with_zoning"):
            _, selected = self.graph.resolve({"mode": "dbt_only", "model": root})
            with self.assertRaises(AirflowSkipException):
                chooser(
                    ti=SimpleNamespace(
                        xcom_pull=lambda **k: {"execute_ids": list(selected)}
                    )
                )
        for root in (
            "dim_building",
            "int_suumo__building_lookup_candidates",
            "int_suumo__zoning_inputs",
        ):
            _, selected = self.graph.resolve({"mode": "dbt_only", "model": root})
            self.assertEqual(
                chooser(
                    ti=SimpleNamespace(
                        xcom_pull=lambda **k: {"execute_ids": list(selected)}
                    )
                ),
                {"mode": "reuse_source"},
            )
        with self.assertRaises(ValueError):
            self.graph.resolve(
                {"mode": "dbt_only", "model": "int_mlit__zoning_matches"}
            )


if __name__ == "__main__":
    unittest.main()
