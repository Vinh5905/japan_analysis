"""Run in the Airflow image: graph, selection and operational regressions."""
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from airflow.exceptions import AirflowSkipException
from airflow.models import DagBag
from airflow.utils.dag_cycle_tester import check_cycle

from dbt_airflow.manifest import assert_fresh, load_manifest, project_fingerprint
from dbt_airflow.operators import SelectedDbtRunOperator, SelectedDbtTestOperator
from dbt_airflow.selection import Selection


class AirflowGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = Path(os.getenv('DBT_PROJECT_DIR', '/opt/airflow/dbt'))
        cls.manifest = load_manifest(cls.project)
        cls.graph = Selection(cls.manifest)
        cls.bag = DagBag('/opt/airflow/dags', include_examples=False)
        cls.dag = cls.bag.get_dag('suumo_load_to_warehouse')

    def test_import_coverage_dependencies_and_stability(self):
        self.assertEqual(self.bag.import_errors, {})
        check_cycle(self.dag)
        models = [t for t in self.dag.tasks if isinstance(t, SelectedDbtRunOperator)]
        tests = [t for t in self.dag.tasks if isinstance(t, SelectedDbtTestOperator)]
        self.assertEqual(len(models), 26)
        counts = Counter(uid for t in tests for uid in t.dbt_node_ids)
        self.assertEqual(counts, Counter({uid: 1 for uid in set(self.graph.tests) | set(self.graph.units)}))
        self.assertEqual(len(self.graph.tests), 88)
        self.assertEqual(len(self.graph.units), 2)
        self.assertNotIn('dbt_run', self.dag.task_ids)
        self.assertNotIn('dbt_test', self.dag.task_ids)
        tasks = {uid: t for t in models for uid in t.dbt_node_ids}
        test_tasks = {uid: t for t in tests for uid in t.dbt_node_ids}
        for uid, run in tasks.items():
            upstream = {t.task_id for t in run.get_flat_relatives(upstream=True)}
            for parent in self.graph.models[uid]['depends_on']['nodes']:
                if parent in tasks:
                    self.assertIn(tasks[parent].task_id, upstream)
                    for tid, test in self.graph.tests.items():
                        if test['depends_on']['nodes'] == [parent]:
                            self.assertIn(test_tasks[tid].task_id, upstream)
            for tid, test in self.graph.tests.items():
                parents = set(test['depends_on']['nodes'])
                if len(parents) > 1 and parents.issubset(self.graph.ancestors(uid)):
                    self.assertIn(test_tasks[tid].task_id, upstream)
        for tid, unit in self.graph.units.items():
            model_task = tasks[self.graph.names[unit['model']]]
            self.assertIn(test_tasks[tid].task_id, model_task.upstream_task_ids)
        for t in models + tests:
            self.assertEqual(t.trigger_rule, 'none_failed')
            self.assertEqual(t.retries, 0)
            self.assertFalse(t.emit_datasets)
            self.assertFalse(t.partial_parse)
            self.assertEqual(t.dbt_cmd_flags, ['--threads', '1'])
        second = DagBag('/opt/airflow/dags', include_examples=False).get_dag(self.dag.dag_id)
        self.assertEqual(sorted(self.dag.task_ids), sorted(second.task_ids))
        self.assertEqual(self.dag.max_active_runs, 1)
        self.assertEqual(self.dag.max_active_tasks, 4)
        report = self.dag.get_task('report_batch_failures')
        self.assertEqual(report.trigger_rule, 'all_done')
        self.assertEqual(report.upstream_task_ids, set(self.dag.task_ids) - {report.task_id})

    def test_address_selection_reuses_upstream(self):
        _, selected = self.graph.resolve({'mode': 'dbt_only', 'model': 'int_suumo__address'})
        root = self.graph.names['int_suumo__address']
        self.assertIn(root, selected)
        self.assertNotIn(self.graph.names['stg_suumo_parser_records'], selected)
        self.assertNotIn(self.graph.names['int_suumo__costs'], selected)
        self.assertEqual(selected, {uid for uid in self.graph.models if uid == root or root in self.graph.ancestors(uid)})
        reused = self.graph.reused_relations(selected)
        self.assertIn(self.graph.names['int_suumo__costs'], reused)
        self.assertTrue(all(uid not in selected for uid in reused))
        for uid, node in self.graph.tests.items():
            parents = set(node['depends_on']['nodes'])
            self.assertEqual(self.graph.test_is_selected(uid, selected),
                             not parents.intersection(self.graph.models) or bool(parents.intersection(selected)))

    def test_invalid_conf(self):
        for conf in ({'mode': 'invalid'}, {'mode': 'dbt_only', 'model': 'int_suumo__address+'},
                     {'model': 'int_suumo__address'}, {'mode': 'dbt_only', 'model': ['a']}):
            with self.assertRaises(ValueError):
                self.graph.resolve(conf)

    def test_batch_and_final_failure_paths(self):
        loader = self.dag.get_task('load_batches').python_callable
        prepare = self.dag.get_task('prepare_transform').python_callable
        report = self.dag.get_task('report_batch_failures').python_callable
        module = __import__(loader.__module__, fromlist=['load_pending_batches'])
        for summary in ({'loaded_batch_ids': [], 'results': []},
                        {'loaded_batch_ids': [], 'results': [{'batch_id': 9, 'status': 'failed'}]}):
            context = {'params': {}, 'ti': SimpleNamespace(xcom_pull=lambda **k: summary)}
            with self.assertRaises(AirflowSkipException):
                prepare(**context)
        for summary in ({'loaded_batch_ids': [1], 'results': [{'batch_id': 1, 'status': 'success'}]},
                        {'loaded_batch_ids': [1], 'results': [{'batch_id': 9, 'status': 'failed'}]}):
            with patch.object(module, 'postgres_connection') as conn:
                conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = ('exists',)
                result = prepare(params={}, ti=SimpleNamespace(xcom_pull=lambda **k: summary))
                self.assertEqual(len(set(result['execute_ids']).intersection(self.graph.models)), 26)
        with patch.object(module, 'load_pending_batches', side_effect=AssertionError('source touched')):
            self.assertEqual(loader(params={'mode': 'dbt_only'})['results'], [])
        for summary, states in ((None, [('load_batches', 'failed')]),
                                ({'results': [{'batch_id': 9, 'status': 'failed'}]}, []),
                                ({'results': []}, [('a.run', 'failed'), ('b.run', 'upstream_failed')])):
            instances = [SimpleNamespace(task_id=t, state=s) for t, s in states]
            with self.assertRaises(RuntimeError):
                report(ti=SimpleNamespace(xcom_pull=lambda **k: summary),
                       dag_run=SimpleNamespace(get_task_instances=lambda: instances))
        report(ti=SimpleNamespace(xcom_pull=lambda **k: {'results': []}),
               dag_run=SimpleNamespace(get_task_instances=lambda: []))
        with patch.object(module, 'postgres_connection') as conn:
            conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (None,)
            with self.assertRaisesRegex(RuntimeError, 'Missing reused upstream relations'):
                prepare(params={'mode': 'dbt_only', 'model': 'int_suumo__address'}, ti=SimpleNamespace(xcom_pull=lambda **k: None))

    def test_fingerprint_prevents_stale_execution(self):
        with tempfile.TemporaryDirectory() as root:
            project = Path(root)
            (project / 'models').mkdir()
            model = project / 'models/a.sql'
            model.write_text('select 1')
            fingerprint = project_fingerprint(project)
            (project / 'target/airflow').mkdir(parents=True)
            (project / 'target/airflow/manifest.json').write_text(json.dumps({'_airflow': {'fingerprint': fingerprint}}))
            assert_fresh(project, fingerprint)
            model.write_text('select 2')
            with self.assertRaisesRegex(RuntimeError, 'dbt-airflow-manifest'):
                assert_fresh(project, fingerprint)


if __name__ == '__main__':
    unittest.main()
