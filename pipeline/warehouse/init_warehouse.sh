#!/bin/sh
set -eu

# This script is idempotent: it creates the warehouse database and raw schema
# objects when they do not exist, without deleting existing data.

: "${WAREHOUSE_POSTGRES_HOST:=warehouse-postgres}"
: "${WAREHOUSE_POSTGRES_PORT:=5432}"
: "${PIPELINE_POSTGRES_USER:=pipeline_admin}"
: "${PIPELINE_POSTGRES_PASSWORD:=pipeline_password_change_me}"
: "${AIRFLOW_DB:=airflow_metadata}"
: "${WAREHOUSE_DB:=japan_warehouse}"

export PGPASSWORD="${PIPELINE_POSTGRES_PASSWORD}"

db_exists="$(psql \
  -h "${WAREHOUSE_POSTGRES_HOST}" \
  -p "${WAREHOUSE_POSTGRES_PORT}" \
  -U "${PIPELINE_POSTGRES_USER}" \
  -d "${AIRFLOW_DB}" \
  -tAc "SELECT 1 FROM pg_database WHERE datname = '${WAREHOUSE_DB}'")"

if [ "${db_exists}" != "1" ]; then
  createdb \
    -h "${WAREHOUSE_POSTGRES_HOST}" \
    -p "${WAREHOUSE_POSTGRES_PORT}" \
    -U "${PIPELINE_POSTGRES_USER}" \
    "${WAREHOUSE_DB}"
fi

psql \
  -h "${WAREHOUSE_POSTGRES_HOST}" \
  -p "${WAREHOUSE_POSTGRES_PORT}" \
  -U "${PIPELINE_POSTGRES_USER}" \
  -d "${WAREHOUSE_DB}" \
  -v ON_ERROR_STOP=1 <<'SQL'
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE IF NOT EXISTS raw.suumo_parser_records (
    task_id BIGINT PRIMARY KEY,
    batch_id BIGINT NOT NULL,
    source_id BIGINT NOT NULL,
    data_hash TEXT NOT NULL,
    record JSONB NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_suumo_parser_records_is_valid
        CHECK ((record ->> 'is_valid')::boolean IS TRUE)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'chk_suumo_parser_records_is_valid'
          AND conrelid = 'raw.suumo_parser_records'::regclass
    ) THEN
        ALTER TABLE raw.suumo_parser_records
            ADD CONSTRAINT chk_suumo_parser_records_is_valid
            CHECK ((record ->> 'is_valid')::boolean IS TRUE);
    END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_suumo_parser_records_batch
    ON raw.suumo_parser_records (batch_id);

CREATE INDEX IF NOT EXISTS idx_suumo_parser_records_source
    ON raw.suumo_parser_records (source_id);

CREATE INDEX IF NOT EXISTS idx_suumo_parser_records_data_hash
    ON raw.suumo_parser_records (data_hash);

CREATE INDEX IF NOT EXISTS idx_suumo_parser_records_record_gin
    ON raw.suumo_parser_records USING GIN (record);
SQL
