\echo Running migration 004_remove_crawl_run_status_and_started_at.sql

-- crawl_runs now records run identity, source, created_at, finished_at, and the
-- number of task rows added during the run. Per-URL state lives in crawl_tasks.

BEGIN;

DROP INDEX IF EXISTS idx_crawl_runs_status;
DROP INDEX IF EXISTS idx_crawl_runs_source_started_at;

ALTER TABLE crawl_runs
    DROP COLUMN IF EXISTS status,
    DROP COLUMN IF EXISTS started_at;

DROP TYPE IF EXISTS crawl_run_status_enum;

CREATE INDEX IF NOT EXISTS idx_crawl_runs_source_created_at
    ON crawl_runs (source_id, created_at DESC);

COMMIT;

\echo Finished migration 004_remove_crawl_run_status_and_started_at.sql
