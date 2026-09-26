"""Check that rebuilding the local mart from unchanged history is idempotent.

Run inside dbt-runner with the normal warehouse environment. Only SELECTs use
psycopg; all materialization is performed by dbt. No fixture data is inserted.
"""

import os
import subprocess

import psycopg
from psycopg import sql

RELATIONS = (
    'dim_date', 'dim_geography', 'dim_rental_listing',
    'dim_observation_quality', 'dim_station_label',
    'fct_rental_price_observation', 'bridge_observation_station_access',
    'rental_price_observations', 'rental_prices_latest_known',
    'rental_price_mart_rejects',
)


def fingerprints():
    """Return order-independent row fingerprints without printing business rows."""
    with psycopg.connect(
        host=os.environ['WAREHOUSE_POSTGRES_HOST'],
        port=os.environ.get('WAREHOUSE_POSTGRES_PORT', '5432'),
        dbname=os.environ['WAREHOUSE_DB'],
        user=os.environ['PIPELINE_POSTGRES_USER'],
        password=os.environ['PIPELINE_POSTGRES_PASSWORD'],
    ) as connection:
        result = {}
        for name in RELATIONS:
            query = sql.SQL('''
                select count(*), md5(coalesce(string_agg(payload, '' order by payload), ''))
                from (select to_jsonb(t)::text as payload from {} t) rows
            ''').format(sql.Identifier('mart', name))
            result[name] = connection.execute(query).fetchone()
        return result


def main():
    """Rebuild the complete mart dependency branch and compare all output rows."""
    before = fingerprints()
    subprocess.run([
        'dbt', 'build', '--select', 'int_suumo__mart_observations+',
        'rental_price_mart_rejects', 'assert_suumo_mart_scd_scenarios',
        'assert_suumo_mart_fee_semantics',
    ], cwd=os.environ.get('DBT_PROJECT_DIR', '/opt/airflow/dbt'), check=True)
    after = fingerprints()
    if before != after:
        changed = [name for name in RELATIONS if before[name] != after[name]]
        raise AssertionError(f'Mart changed on identical input: {changed}')
    print('PASS: identical rows and keys after rebuild for all 10 mart relations')
    print({name: value[0] for name, value in after.items()})


if __name__ == '__main__':
    main()
