-- Crawler metadata fresh schema.
--
-- This init file is the latest schema for a new local database. Use
-- docker/postgres/migrations/*.sql for existing databases.

BEGIN;

DROP SCHEMA IF EXISTS crawler CASCADE;

DROP TABLE IF EXISTS load_batches CASCADE;
DROP TABLE IF EXISTS parser_records CASCADE;
DROP TABLE IF EXISTS parsed_records CASCADE;
DROP TABLE IF EXISTS crawl_tasks CASCADE;
DROP TABLE IF EXISTS raw_snapshots CASCADE;
DROP TABLE IF EXISTS crawl_runs CASCADE;
DROP TABLE IF EXISTS crawl_sources CASCADE;
DROP TABLE IF EXISTS config CASCADE;
DROP TABLE IF EXISTS suumo_rental_raw CASCADE;

DROP FUNCTION IF EXISTS set_updated_at() CASCADE;

DROP TYPE IF EXISTS load_batch_status_enum CASCADE;
DROP TYPE IF EXISTS raw_content_type_enum CASCADE;
DROP TYPE IF EXISTS crawl_task_status_enum CASCADE;
DROP TYPE IF EXISTS http_method_enum CASCADE;
DROP TYPE IF EXISTS run_created_by_enum CASCADE;
DROP TYPE IF EXISTS crawl_run_status_enum CASCADE;
DROP TYPE IF EXISTS robots_policy_enum CASCADE;

CREATE TYPE robots_policy_enum AS ENUM (
    'allowed',
    'disallowed',
    'limited',
    'not_applicable'
);

CREATE TYPE run_created_by_enum AS ENUM (
    'schedule',
    'manual'
);

CREATE TYPE http_method_enum AS ENUM (
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'HEAD',
    'OPTIONS'
);

CREATE TYPE crawl_task_status_enum AS ENUM (
    'failed',
    'cancelled',
    'pending',
    'success'
);

CREATE TYPE raw_content_type_enum AS ENUM (
    'application/json',
    'text/html'
);

CREATE TYPE load_batch_status_enum AS ENUM (
    'pending',
    'loading',
    'success',
    'failed'
);

CREATE TABLE config (
    config_id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (config_id = 1),
    max_retries INTEGER NOT NULL DEFAULT 10 CHECK (max_retries >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crawl_sources (
    source_id BIGSERIAL PRIMARY KEY,
    source_key TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    crawl_frequency TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    robots_policy robots_policy_enum NOT NULL DEFAULT 'allowed',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crawl_runs (
    run_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    finished_at TIMESTAMPTZ,
    total_urls INTEGER NOT NULL DEFAULT 0 CHECK (total_urls >= 0),
    created_by run_created_by_enum NOT NULL DEFAULT 'schedule',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE raw_snapshots (
    raw_snapshot_id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    final_url TEXT,
    http_status INTEGER CHECK (http_status BETWEEN 100 AND 599),
    content_type raw_content_type_enum NOT NULL,
    content_length BIGINT NOT NULL CHECK (content_length >= 0),
    content_hash TEXT NOT NULL CHECK (content_hash ~ '^[a-f0-9]{64}$'),
    storage_path TEXT NOT NULL UNIQUE,
    compression TEXT,
    encoding TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crawl_tasks (
    task_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
    url TEXT NOT NULL,
    url_hash TEXT NOT NULL CHECK (url_hash ~ '^[a-f0-9]{64}$'),
    method http_method_enum NOT NULL DEFAULT 'GET',
    status crawl_task_status_enum NOT NULL DEFAULT 'pending',
    error_type TEXT,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    fetched_at TIMESTAMPTZ,
    raw_snapshot_id BIGINT REFERENCES raw_snapshots (raw_snapshot_id),
    batch_id BIGINT,
    CHECK (fetched_at IS NULL OR fetched_at >= scheduled_at)
);

CREATE TABLE load_batches (
    batch_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    file_path TEXT NOT NULL UNIQUE,
    file_format TEXT NOT NULL,
    compression TEXT,
    row_count INTEGER NOT NULL CHECK (row_count >= 0),
    file_hash TEXT NOT NULL CHECK (file_hash ~ '^[a-f0-9]{64}$'),
    status load_batch_status_enum NOT NULL DEFAULT 'pending',
    inserted_count INTEGER NOT NULL DEFAULT 0 CHECK (inserted_count >= 0),
    updated_count INTEGER NOT NULL DEFAULT 0 CHECK (updated_count >= 0),
    skipped_count INTEGER NOT NULL DEFAULT 0 CHECK (skipped_count >= 0),
    failed_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_loading_at TIMESTAMPTZ,
    finished_loading_at TIMESTAMPTZ,
    loaded_at TIMESTAMPTZ,
    CHECK (started_loading_at IS NULL OR started_loading_at >= created_at),
    CHECK (
        finished_loading_at IS NULL
        OR started_loading_at IS NULL
        OR finished_loading_at >= started_loading_at
    ),
    CHECK (loaded_at IS NULL OR finished_loading_at IS NULL OR loaded_at <= finished_loading_at)
);

ALTER TABLE crawl_tasks
    ADD CONSTRAINT fk_crawl_tasks_batch_id
    FOREIGN KEY (batch_id)
    REFERENCES load_batches (batch_id);

CREATE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_config_updated_at
    BEFORE UPDATE ON config
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_crawl_sources_updated_at
    BEFORE UPDATE ON crawl_sources
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();

CREATE INDEX idx_crawl_sources_robots_policy
    ON crawl_sources (robots_policy);

CREATE INDEX idx_crawl_runs_source_created_at
    ON crawl_runs (source_id, created_at DESC);

CREATE INDEX idx_crawl_tasks_run_status
    ON crawl_tasks (run_id, status);

CREATE UNIQUE INDEX idx_crawl_tasks_run_url_hash
    ON crawl_tasks (run_id, url_hash);

CREATE INDEX idx_crawl_tasks_url_hash_status
    ON crawl_tasks (url_hash, status);

CREATE INDEX idx_crawl_tasks_raw_snapshot
    ON crawl_tasks (raw_snapshot_id);

CREATE INDEX idx_crawl_tasks_batch
    ON crawl_tasks (batch_id)
    WHERE batch_id IS NOT NULL;

CREATE INDEX idx_raw_snapshots_content_hash
    ON raw_snapshots (content_hash);

CREATE INDEX idx_load_batches_source_status
    ON load_batches (source_id, status);

CREATE INDEX idx_load_batches_file_hash
    ON load_batches (file_hash);

INSERT INTO config (config_id, max_retries)
VALUES (1, 10);

INSERT INTO crawl_sources (
    source_id,
    source_key,
    source_name,
    base_url,
    crawl_frequency,
    robots_policy,
    notes
)
VALUES (
    1,
    'suumo',
    'SUUMO',
    'https://suumo.jp',
    'schedule',
    'allowed',
    NULL
);

SELECT setval(
    pg_get_serial_sequence('crawl_sources', 'source_id'),
    COALESCE((SELECT MAX(source_id) FROM crawl_sources), 1),
    true
);

COMMIT;
