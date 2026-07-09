CREATE SCHEMA IF NOT EXISTS crawler;

CREATE TABLE IF NOT EXISTS crawler.ingestion_runs (
    id BIGSERIAL PRIMARY KEY,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_source_started_at
    ON crawler.ingestion_runs (source_name, started_at DESC);

