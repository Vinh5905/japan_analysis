-- Crawler metadata fresh schema.
--
-- This init file is the source of truth for a new local database. It is
-- intentionally destructive when run manually because migrations are not used
-- for this reset-style schema rewrite.

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

CREATE TYPE crawl_run_status_enum AS ENUM (
    'running',
    'success',
    'failed',
    'cancelled'
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
    robots_policy robots_policy_enum NOT NULL DEFAULT 'limited',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE crawl_runs (
    run_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    status crawl_run_status_enum NOT NULL DEFAULT 'running',
    total_urls INTEGER NOT NULL DEFAULT 0 CHECK (total_urls >= 0),
    success_count INTEGER NOT NULL DEFAULT 0 CHECK (success_count >= 0),
    failed_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_count >= 0),
    created_by run_created_by_enum NOT NULL DEFAULT 'schedule',
    new_urls_file_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (finished_at IS NULL OR finished_at >= started_at)
);

CREATE TABLE raw_snapshots (
    raw_snapshot_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
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
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    url TEXT NOT NULL,
    url_hash TEXT NOT NULL UNIQUE CHECK (url_hash ~ '^[a-f0-9]{64}$'),
    method http_method_enum NOT NULL DEFAULT 'GET',
    status crawl_task_status_enum NOT NULL DEFAULT 'pending',
    error_type TEXT,
    error_message TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    fetched_at TIMESTAMPTZ,
    raw_snapshot_id BIGINT REFERENCES raw_snapshots (raw_snapshot_id),
    CHECK (fetched_at IS NULL OR fetched_at >= scheduled_at)
);

CREATE TABLE parser_records (
    record_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL DEFAULT 1 REFERENCES crawl_sources (source_id),
    task_id BIGINT REFERENCES crawl_tasks (task_id),
    raw_snapshot_id BIGINT NOT NULL REFERENCES raw_snapshots (raw_snapshot_id),
    source_record_id TEXT,
    image_public_url TEXT,
    image_storage_path TEXT,
    "敷金" TEXT,
    "管理費・共益費" TEXT,
    "礼金" TEXT,
    "保証金" TEXT,
    "敷引・償却" TEXT,
    "所在地" TEXT,
    "駅徒歩" TEXT,
    "間取り" TEXT,
    "専有面積" TEXT,
    "築年数" TEXT,
    "階" TEXT,
    "向き" TEXT,
    "建物種別" TEXT,
    "間取り詳細" TEXT,
    "構造" TEXT,
    "階建" TEXT,
    "築年月" TEXT,
    "エネルギー消費性能" TEXT,
    "目安光熱費" TEXT,
    "損保" TEXT,
    "駐車場" TEXT,
    "入居" TEXT,
    "条件" TEXT,
    "SUUMO物件コード" TEXT,
    "情報更新日" TEXT,
    "契約期間" TEXT,
    "仲介手数料" TEXT,
    "保証会社" TEXT,
    "ほか初期費用" TEXT,
    "ほか諸費用" TEXT,
    "取引態様" TEXT,
    "取り扱い店舗物件コード" TEXT,
    "総戸数" TEXT,
    "次回更新予定日" TEXT,
    data_hash TEXT CHECK (data_hash IS NULL OR data_hash ~ '^[a-f0-9]{64}$'),
    parsed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_valid BOOLEAN NOT NULL DEFAULT FALSE,
    error_type TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (
        is_valid = FALSE
        OR (data_hash IS NOT NULL AND error_type IS NULL AND error_message IS NULL)
    )
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

CREATE INDEX idx_crawl_runs_source_started_at
    ON crawl_runs (source_id, started_at DESC);

CREATE INDEX idx_crawl_runs_status
    ON crawl_runs (status);

CREATE INDEX idx_crawl_tasks_run_status
    ON crawl_tasks (run_id, status);

CREATE INDEX idx_crawl_tasks_source_status
    ON crawl_tasks (source_id, status);

CREATE INDEX idx_crawl_tasks_raw_snapshot
    ON crawl_tasks (raw_snapshot_id);

CREATE INDEX idx_raw_snapshots_source_created_at
    ON raw_snapshots (source_id, created_at DESC);

CREATE INDEX idx_raw_snapshots_run
    ON raw_snapshots (run_id);

CREATE INDEX idx_raw_snapshots_content_hash
    ON raw_snapshots (content_hash);

CREATE INDEX idx_parser_records_source_record
    ON parser_records (source_id, source_record_id);

CREATE INDEX idx_parser_records_task
    ON parser_records (task_id);

CREATE INDEX idx_parser_records_raw_snapshot
    ON parser_records (raw_snapshot_id);

CREATE INDEX idx_parser_records_data_hash
    ON parser_records (data_hash);

CREATE INDEX idx_parser_records_valid
    ON parser_records (is_valid);

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
    'limited',
    'Default SUUMO rental source. Detail URLs are stored without the base URL.'
);

SELECT setval(
    pg_get_serial_sequence('crawl_sources', 'source_id'),
    COALESCE((SELECT MAX(source_id) FROM crawl_sources), 1),
    true
);

COMMIT;
