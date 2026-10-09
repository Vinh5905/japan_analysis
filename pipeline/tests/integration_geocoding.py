"""Live local acceptance: scheduler must be stopped; never writes source listings.

Run --cache-miss to evict one saved result temporarily and let the real DAG
repopulate it through HTTP. On failure, restore the saved row. A successful
run retains the newly audited result. Repeat without the flag checks cache hits.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from airflow.models import DagBag
from airflow.utils import timezone
from airflow.utils.dag_cycle_tester import check_cycle
from dbt_airflow.manifest import load_manifest
from dbt_airflow.selection import Selection
from loaders.suumo_batch_loader import load_warehouse_postgres_config, postgres_connection
from loaders.suumo_geocoder import PROVIDER, QUERY_VERSION, read_cache, write_cache_result
from verify_geocode_warehouse import fingerprints


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache-miss',action='store_true')
    parser.add_argument('--executor',action='store_true',help='Use configured LocalExecutor, maximum DAG concurrency')
    parser.add_argument('--log-file',required=True)
    args=parser.parse_args()
    log=Path(args.log_file)
    log.parent.mkdir(parents=True,exist_ok=True)
    sys.stdout=log.open('w',buffering=1)
    sys.stderr=sys.stdout
    project=Path('/opt/airflow/dbt')
    graph=Selection(load_manifest(project))
    baseline=json.loads((project/'target/airflow/geocode_business_baseline.json').read_text())
    before=fingerprints(baseline)
    bag=DagBag('/opt/airflow/dags',include_examples=False)
    assert not bag.import_errors,bag.import_errors
    dag=bag.get_dag('suumo_load_to_warehouse')
    check_cycle(dag)
    config=load_warehouse_postgres_config()
    backup=None
    success=False
    try:
        if args.cache_miss:
            with postgres_connection(config) as conn:
                cache=read_cache(conn)
                query='大阪府大阪市淀川区西宮原1丁目'
                backup=cache[query]
                conn.execute('delete from raw.suumo_address_geocodes where provider=%s and query_version=%s and address_query=%s',
                             (PROVIDER,QUERY_VERSION,query))
        run=dag.test(execution_date=timezone.utcnow(),run_conf={'mode':'dbt_only','model':'dim_geography'},use_executor=args.executor)
        states={ti.task_id:ti.state for ti in run.get_task_instances()}
        assert run.state=='success',(run.state,states)
        summary=run.get_task_instance('enrich_geographies_cache').xcom_pull(task_ids='enrich_geographies_cache')
        if args.cache_miss:
            assert summary['new_addresses']==1 and summary['lookups']==1 and summary['matched']==1,summary
        else:
            assert summary['lookups']==0 and summary['cache_hits']==before['mart.dim_geography']['count'],summary
        assert fingerprints(baseline)==before,'Existing business rows/keys changed'
        with postgres_connection(config) as conn:
            assert conn.execute("select count(*) from mart.dim_geography where geocode_status='matched' and latitude is not null and longitude is not null").fetchone()[0]==before['mart.dim_geography']['count']
            assert conn.execute('select count(*) from analytics.rental_listing_latest where latitude is not null and longitude is not null').fetchone()[0]==before['analytics.rental_listing_latest']['count']
        _,selected=graph.resolve({'mode':'dbt_only','model':'dim_geography'})
        for uid in graph.models.keys()-selected:
            # No upstream model rebuild: only existing mart observations are reused.
            tasks=[t for t in dag.tasks if uid in getattr(t,'dbt_node_ids',[]) and t.task_id.endswith('.run')]
            assert all(states[t.task_id]=='skipped' for t in tasks),(uid,states)
        success=True
        report={'state':run.state,'run_id':run.run_id,'cache_miss':args.cache_miss,
                'enrichment':summary,'task_states':dict(Counter(states.values()))}
        (project/'target/airflow'/('geocode-cache-miss.json' if args.cache_miss else 'geocode-repeat.json')).write_text(json.dumps(report,indent=2))
        message='GEOCODE QA PASS '+json.dumps(report)
        print(message)
        sys.__stdout__.write(message+'\n')
    finally:
        if backup and not success:
            with postgres_connection(config) as conn:write_cache_result(conn,backup)


if __name__=='__main__':main()
