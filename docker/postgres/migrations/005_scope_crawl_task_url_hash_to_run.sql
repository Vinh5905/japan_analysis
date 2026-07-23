\echo Running migration 005_scope_crawl_task_url_hash_to_run.sql

-- URL hashes can repeat across runs for future manual rerun flows, while one run
-- still has at most one task row per URL hash.

BEGIN;

ALTER TABLE crawl_tasks
    DROP CONSTRAINT IF EXISTS crawl_tasks_url_hash_key;

DROP INDEX IF EXISTS crawl_tasks_url_hash_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_crawl_tasks_run_url_hash
    ON crawl_tasks (run_id, url_hash);

CREATE INDEX IF NOT EXISTS idx_crawl_tasks_url_hash_status
    ON crawl_tasks (url_hash, status);

COMMIT;

\echo Finished migration 005_scope_crawl_task_url_hash_to_run.sql
