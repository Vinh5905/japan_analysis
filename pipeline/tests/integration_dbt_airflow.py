"""Local warehouse QA; stop scheduler first and do not run other dbt writers.

Use --scenario full/address/empty/failure-sql/failure-test/repair. Fault injection
changes only Cosmos's temporary clone, never project SQL or warehouse inputs.
The repair scenario uses the same Airflow Clear APIs as the UI and resumes the
failed run, retaining successful upstream tasks and their artifacts.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import nullcontext
import json
import logging
import os
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import quote
from unittest.mock import patch

# QA should measure local scheduling/SQL, independent of telemetry networking.
os.environ.setdefault('AIRFLOW__COSMOS__ENABLE_TELEMETRY', 'False')

if '--executor' in sys.argv:
    # DAG.test holds an open metadata session. Its forked CLI workers must
    # start fresh interpreters rather than inherit that PostgreSQL connection.
    os.environ['AIRFLOW__CORE__EXECUTE_TASKS_NEW_PYTHON_INTERPRETER'] = 'True'

if '--log-file' in sys.argv:
    log_path = Path(sys.argv[sys.argv.index('--log-file') + 1])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout = log_path.open('w', buffering=1)
    sys.stderr = sys.stdout

from airflow.models import DagBag, DagRun
from airflow.models.dag import _run_task
from airflow.executors.executor_loader import ExecutorLoader
from airflow.utils import timezone
from airflow.utils.session import create_session
from airflow.utils.state import DagRunState, TaskInstanceState
from psycopg import sql

from dbt_airflow.manifest import load_manifest
from dbt_airflow.operators import ArtifactTask, SelectedDbtRunOperator, SelectedDbtTestOperator
from dbt_airflow.selection import Selection
from loaders.suumo_batch_loader import load_warehouse_postgres_config, postgres_connection

PROJECT = Path(os.getenv('DBT_PROJECT_DIR', '/opt/airflow/dbt'))
QA_DIR = PROJECT / 'target/airflow/qa'
MANIFEST = load_manifest(PROJECT)
GRAPH = Selection(MANIFEST)


def fingerprints(allow_missing=False):
    result = {}
    with postgres_connection(load_warehouse_postgres_config()) as conn:
        with conn.cursor() as cursor:
            for uid, node in GRAPH.nodes.items():
                if node['resource_type'] not in {'model', 'source', 'seed'}:
                    continue
                if allow_missing:
                    cursor.execute('select to_regclass(%s)', (node['relation_name'],))
                    if cursor.fetchone()[0] is None:
                        result[uid] = None
                        continue
                cursor.execute(sql.SQL("select count(*), md5(coalesce(string_agg(payload, '' order by payload), '')) from (select to_jsonb(t)::text as payload from {} t) rows").format(sql.Identifier(node['schema'], node['alias'] if 'alias' in node else node['identifier'])))
                result[uid] = list(cursor.fetchone())
    return result


def artifact_results(run_id):
    root = Path('/opt/airflow/logs/dbt_artifacts') / 'suumo_load_to_warehouse' / quote(run_id, safe='')
    counts = Counter()
    for task in root.iterdir():
        attempts = sorted(task.glob('attempt=*'), key=lambda p: int(p.name.split('=')[1]))
        path = attempts[-1] / 'target/run_results.json'
        if path.exists():
            for item in json.loads(path.read_text())['results']:
                counts[item['unique_id']] += 1
    return counts


def fault_clone(kind):
    original = SelectedDbtRunOperator._clone_project

    def inject(operator, destination):
        original(operator, destination)
        uid = 'model.japan_analysis.int_suumo__address' if kind == 'sql' else 'test.japan_analysis.assert_suumo_history_task_coverage'
        if uid not in operator.dbt_node_ids:
            return
        relative = Path(GRAPH.nodes[uid]['original_file_path'])
        top = destination / relative.parts[0]
        # Cosmos links whole folders; replace the link with a private copy.
        assert top.is_symlink()
        top.unlink()
        shutil.copytree(PROJECT / relative.parts[0], top)
        (destination / relative).write_text('select intentional_qa_missing_column as task_id' if kind == 'sql' else 'select 1 as intentional_qa_failure')
    return inject


def resume(dag, run_id, use_executor=False):
    with create_session() as session:
        run = session.query(DagRun).filter_by(dag_id=dag.dag_id, run_id=run_id).one()
        run.dag = dag
        failed = [ti.task_id for ti in run.get_task_instances(session=session) if ti.state in {'failed', 'upstream_failed'}]
        subdag = dag.partial_subset(task_ids_or_regex=failed, include_downstream=True, include_upstream=False)
        retained = {ti.task_id: (ti.state, ti.try_number) for ti in run.get_task_instances(session=session)
                    if ti.task_id not in subdag.task_ids}
        subdag.clear(start_date=run.execution_date, end_date=run.execution_date, session=session)
        run.state = DagRunState.RUNNING
        session.commit()
        executor = ExecutorLoader.get_default_executor() if use_executor else None
        if executor:
            executor.start()
        try:
            while run.state == DagRunState.RUNNING:
                session.expire_all()
                ready, _ = run.update_state(session=session)
                if not executor and not ready and run.state == DagRunState.RUNNING:
                    raise AssertionError('Repair deadlocked')
                for ti in ready:
                    ti.task = dag.get_task(ti.task_id)
                    ti.try_number += 1
                    ti.state = TaskInstanceState.SCHEDULED
                    session.commit()
                    if not executor:
                        _run_task(ti, session=session)
                if executor:
                    for ti in run.get_task_instances(session=session, state=TaskInstanceState.SCHEDULED):
                        ti.task = dag.get_task(ti.task_id)
                        if not executor.has_task(ti):
                            executor.queue_task_instance(ti, ignore_ti_state=True)
                    executor.heartbeat()
                    if run.state == DagRunState.RUNNING:
                        time.sleep(1)
        finally:
            if executor:
                executor.end()
        assert run.state == DagRunState.SUCCESS, run.state
        after = {ti.task_id: (ti.state, ti.try_number) for ti in run.get_task_instances(session=session)}
        assert all(after[task_id] == values for task_id, values in retained.items()), 'Clear reran retained upstream'
        return run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['full', 'address', 'empty', 'failure-sql', 'failure-test', 'repair'], required=True)
    parser.add_argument('--run-id')
    parser.add_argument('--log-file')
    parser.add_argument('--executor', action='store_true', help='Use the configured LocalExecutor (set parallelism=4 for QA)')
    args = parser.parse_args()
    if args.executor and args.scenario.startswith('failure-'):
        raise ValueError('Fault injection runs in-process; use --executor for address/repair QA')
    QA_DIR.mkdir(parents=True, exist_ok=True)
    bag = DagBag('/opt/airflow/dags', include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.get_dag('suumo_load_to_warehouse')
    dag.log.setLevel(logging.ERROR)
    if args.scenario == 'repair':
        original_scenario = next(name for name in ['failure-sql', 'failure-test']
                                 if json.loads((QA_DIR / (name + '.json')).read_text())['run_id'] == args.run_id)
        before = json.loads((QA_DIR / (original_scenario + '-baseline.json')).read_text())
    else:
        before = fingerprints()
    (QA_DIR / (args.scenario + '-baseline.json')).write_text(json.dumps(before, indent=2))
    if args.scenario == 'repair':
        assert args.run_id
        run = resume(dag, args.run_id, use_executor=args.executor)
    else:
        conf = {'mode': 'dbt_only'}
        if args.scenario in {'address', 'failure-sql'}:
            conf['model'] = 'int_suumo__address'
        elif args.scenario == 'failure-test':
            conf['model'] = 'int_suumo_rentals_history'
        elif args.scenario == 'empty':
            conf = {'batch_ids': [9223372036854775807]}
        fault = patch.object(ArtifactTask, '_clone_project', fault_clone(args.scenario.split('-')[1]), create=True) if args.scenario.startswith('failure-') else nullcontext()
        with fault:
            run = dag.test(execution_date=timezone.utcnow(), run_conf=conf, use_executor=args.executor)
    instances = run.get_task_instances()
    states = {ti.task_id: ti.state for ti in instances}
    events = []
    for ti in instances:
        if ti.state == 'success' and isinstance(dag.get_task(ti.task_id), (SelectedDbtRunOperator, SelectedDbtTestOperator)) and ti.start_date and ti.end_date:
            events.extend([(ti.start_date, 1), (ti.end_date, -1)])
    active = peak = 0
    for _, delta in sorted(events):
        active += delta
        peak = max(peak, active)
    if args.executor:
        assert peak <= 4, f'Exceeded four concurrent dbt tasks: {peak}'
    expected_state = 'failed' if args.scenario.startswith('failure-') else 'success'
    assert run.state == expected_state, (run.state, states)
    after = fingerprints(allow_missing=args.scenario.startswith('failure-'))
    if args.scenario.startswith('failure-'):
        # dbt swaps/drop-cascades relations before downstream quality gates.
        # Failed runs may temporarily lose views; Clear must restore them.
        assert all(values is None or values == before[uid] for uid, values in after.items()), 'Existing rows changed during fault QA'
    else:
        assert before == after, 'Warehouse rows/keys changed from baseline'
    counts = artifact_results(run.run_id) if args.scenario != 'empty' else Counter()
    if args.scenario == 'full':
        expected = set(GRAPH.models) | set(GRAPH.tests) | set(GRAPH.units)
        assert counts == Counter({uid: 1 for uid in expected}), counts
    elif args.scenario == 'address':
        _, selected = GRAPH.resolve({'mode': 'dbt_only', 'model': 'int_suumo__address'})
        executed_models = set(counts).intersection(GRAPH.models)
        assert executed_models == selected, (executed_models, selected)
        expected_tests = {uid for uid in GRAPH.tests if GRAPH.test_is_selected(uid, selected)}
        expected_units = {uid for uid, n in GRAPH.units.items() if GRAPH.names[n['model']] in selected}
        assert counts == Counter({uid: 1 for uid in selected | expected_tests | expected_units}), counts
        for t in dag.tasks:
            if isinstance(t, SelectedDbtRunOperator) and not set(t.dbt_node_ids).intersection(selected):
                assert states[t.task_id] == 'skipped', (t.task_id, states[t.task_id])
    elif args.scenario == 'empty':
        assert all(state == 'skipped' for task_id, state in states.items() if '.run' in task_id or task_id.endswith('.test'))
    elif args.scenario.startswith('failure-'):
        assert states['report_batch_failures'] == 'failed'
        assert any(state == 'upstream_failed' for state in states.values())
        target = 'model.japan_analysis.int_suumo__address' if args.scenario == 'failure-sql' else 'test.japan_analysis.assert_suumo_history_task_coverage'
        assert counts[target] == 1, counts
        artifact_root = Path('/opt/airflow/logs/dbt_artifacts') / dag.dag_id / quote(run.run_id, safe='')
        failed_task = next(t for t in dag.tasks if target in getattr(t, 'dbt_node_ids', []))
        assert states[failed_task.task_id] == 'failed'
        failed_artifacts = artifact_root / quote(failed_task.task_id, safe='') / 'attempt=1'
        for relative in ['command.json', 'logs/dbt.log', 'target/run_results.json']:
            assert (failed_artifacts / relative).is_file(), relative
        assert list((failed_artifacts / 'target/compiled').rglob('*.sql'))
        failed_results = json.loads((failed_artifacts / 'target/run_results.json').read_text())['results']
        assert any(item['unique_id'] == target and item['status'] in {'error', 'fail'} for item in failed_results)
    report = {'scenario': args.scenario, 'run_id': run.run_id, 'state': run.state, 'peak_task_concurrency': peak,
              'states': states, 'node_execution_counts': dict(counts), 'missing_relations': [uid for uid, values in after.items() if values is None],
              'baseline_counts': {uid: values[0] for uid, values in before.items()}}
    (QA_DIR / (args.scenario + '.json')).write_text(json.dumps(report, indent=2))
    summary = 'QA PASS ' + json.dumps({'scenario': args.scenario, 'run_id': run.run_id, 'state': run.state, 'nodes': len(counts)})
    print(summary)
    if args.log_file:
        sys.__stdout__.write(summary + '\n')


if __name__ == '__main__':
    main()
