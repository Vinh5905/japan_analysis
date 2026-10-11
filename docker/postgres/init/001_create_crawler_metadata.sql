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
DROP TABLE IF EXISTS crawl_areas CASCADE;
DROP TABLE IF EXISTS crawl_area_catalogs CASCADE;
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
    CHECK (
        loaded_at IS NULL
        OR finished_loading_at IS NULL
        OR loaded_at <= finished_loading_at
    )
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

CREATE TABLE IF NOT EXISTS crawl_area_catalogs (
    source_id BIGINT NOT NULL REFERENCES crawl_sources (source_id),
    scope TEXT NOT NULL, catalog_url TEXT NOT NULL,
    synced_at TIMESTAMPTZ, PRIMARY KEY (source_id, scope)
);
CREATE TABLE IF NOT EXISTS crawl_areas (
    area_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES crawl_sources (source_id),
    prefecture TEXT NOT NULL, district TEXT, municipality TEXT NOT NULL,
    ward TEXT NOT NULL,
    display_name TEXT NOT
    NULL,
    sc TEXT NOT NULL CHECK
    (sc ~ '^[0-9]{5}$'),
    UNIQUE (source_id, prefecture, municipality, ward),
    UNIQUE (source_id, sc) DEFERRABLE INITIALLY DEFERRED
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS area_id BIGINT REFERENCES crawl_areas (
    area_id
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_key TEXT UNIQUE;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS search_url TEXT;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS area_snapshot JSONB;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_status TEXT CHECK (
    pipeline_status IN
    (
        'running',
        'completed',
        'preflight_failed',
        'crawl_failed',
        'cleanup_failed',
        'interrupted'
    )
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS pipeline_finished_at TIMESTAMPTZ;
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS cleanup_confirmed_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS idx_crawl_runs_area_created ON crawl_runs (
    area_id, created_at DESC
);
INSERT INTO crawl_areas (source_id, prefecture, municipality, ward, display_name, sc)
SELECT
    s.source_id,
    '大阪府',
    '大阪市',
    v.ward,
    v.name,
    v.sc
FROM crawl_sources s CROSS JOIN (
    VALUES
    ('都島区', 'Miyakojima', '27102'),
    ('福島区', 'Fukushima', '27103'),
    ('此花区', 'Konohana', '27104'),
    ('西区', 'Nishi', '27106'),
    ('港区', 'Minato', '27107'),
    ('大正区', 'Taisho', '27108'),
    ('天王寺区', 'Tennoji', '27109'),
    ('浪速区', 'Naniwa', '27111'),
    ('西淀川区', 'Nishiyodogawa', '27113'),
    ('東淀川区', 'Higashiyodogawa', '27114'),
    ('東成区', 'Higashinari', '27115'),
    ('生野区', 'Ikuno', '27116'),
    ('旭区', 'Asahi', '27117'),
    ('城東区', 'Joto', '27118'),
    ('阿倍野区', 'Abeno', '27119'),
    ('住吉区', 'Sumiyoshi', '27120'),
    ('東住吉区', 'Higashisumiyoshi', '27121'),
    ('西成区', 'Nishinari', '27122'),
    ('淀川区', 'Yodogawa', '27123'),
    ('鶴見区', 'Tsurumi', '27124'),
    ('住之江区', 'Suminoe', '27125'),
    ('平野区', 'Hirano', '27126'),
    ('北区', 'Kita', '27127'),
    ('中央区', 'Chuo', '27128')
) v (ward, name, sc)
WHERE s.source_key = 'suumo'
ON CONFLICT (source_id, prefecture, municipality, ward) DO NOTHING;
-- Confirmed legacy SUUMO scope: Yodogawa. Do not infer old pipeline results.
UPDATE crawl_runs r SET
    area_id = a.area_id,
    area_snapshot = jsonb_build_object(
        'prefecture', a.prefecture, 'district', a.district,
        'municipality',
        a.municipality,
        'ward',
        a.ward,
        'display_name',
        a.display_name,
        'sc',
        a.sc,
        'area_id',
        a.area_id
    )
FROM crawl_areas a JOIN crawl_sources s ON s.source_id = a.source_id
WHERE
    r.source_id = s.source_id AND s.source_key = 'suumo' AND a.ward = '淀川区'
    AND r.area_id IS NULL AND r.pipeline_key IS NULL;
INSERT INTO crawl_area_catalogs (source_id, scope, catalog_url)
SELECT
    source_id,
    'osaka_city',
    'https://suumo.jp/chintai/osaka/city/'
FROM crawl_sources
WHERE source_key = 'suumo'
ON CONFLICT DO NOTHING;


CREATE TABLE IF NOT EXISTS crawl_vpns (
    vpn_id BIGSERIAL PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE CHECK (filename ~ '^[A-Za-z0-9_.-]+\.ovpn$'),
    relative_path TEXT NOT NULL UNIQUE CHECK (relative_path = filename),
    sha256 TEXT NOT NULL CHECK (sha256 ~ '^[a-f0-9]{64}$'),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    total_requests BIGINT NOT NULL DEFAULT 0 CHECK (total_requests >= 0),
    activation_successes BIGINT NOT NULL DEFAULT 0 CHECK (activation_successes >= 0),
    activation_failures BIGINT NOT NULL DEFAULT 0 CHECK (activation_failures >= 0),
    last_attempt_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS vpn_id BIGINT REFERENCES crawl_vpns (
    vpn_id
);
ALTER TABLE crawl_runs ADD COLUMN IF NOT EXISTS vpn_snapshot JSONB;

CREATE TABLE IF NOT EXISTS crawl_vpn_attempts (
    attempt_id BIGSERIAL PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
    vpn_id BIGINT NOT NULL REFERENCES crawl_vpns (vpn_id),
    snapshot JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'success', 'failed', 'interrupted')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    UNIQUE (run_id, vpn_id)
);

CREATE TABLE IF NOT EXISTS crawl_vpn_requests (
    request_id UUID PRIMARY KEY,
    run_id BIGINT NOT NULL REFERENCES crawl_runs (run_id),
    vpn_id BIGINT NOT NULL REFERENCES crawl_vpns (vpn_id),
    stage TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS crawl_vpn_requests_run_idx ON crawl_vpn_requests (run_id);
CREATE INDEX IF NOT EXISTS crawl_vpn_attempts_pending_idx ON crawl_vpn_attempts (
    run_id
) WHERE status
= 'pending';

-- A single idempotent transaction records each downloader attempt and its counter.
-- Historical HTML totals cannot be backfilled into HTTP request counts.
CREATE OR REPLACE FUNCTION record_crawl_vpn_request(
    p_request UUID, p_run BIGINT, p_vpn BIGINT, p_stage TEXT
)
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
DECLARE added INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM crawl_runs r JOIN crawl_vpn_attempts a
        ON a.run_id=r.run_id AND a.vpn_id=r.vpn_id
        WHERE r.run_id=p_run AND r.vpn_id=p_vpn AND r.pipeline_status='running'
          AND r.cleanup_confirmed_at IS NULL AND a.status='success') THEN
        RAISE EXCEPTION 'No verified VPN context for run';
    END IF;
    INSERT INTO crawl_vpn_requests(request_id,run_id,vpn_id,stage)
        VALUES(p_request,p_run,p_vpn,p_stage) ON CONFLICT(request_id) DO NOTHING;
    GET DIAGNOSTICS added = ROW_COUNT;
    IF added=1 THEN
        UPDATE crawl_vpns SET total_requests=total_requests+1 WHERE vpn_id=p_vpn;
    ELSIF NOT EXISTS (SELECT 1 FROM crawl_vpn_requests WHERE request_id=p_request
        AND run_id=p_run AND vpn_id=p_vpn AND stage=p_stage) THEN
        RAISE EXCEPTION 'Request identity reused with different context';
    END IF;
    RETURN added=1;
END $$;

COMMIT;
