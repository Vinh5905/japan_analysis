\echo Running migration 001_drop_crawl_runs_derived_counts.sql

-- Remove crawl run fields that are now derived from crawl_tasks/raw files.
-- This migration is idempotent so local databases can be migrated safely after
-- a fresh bootstrap or after a partial manual schema update.

BEGIN;

ALTER TABLE crawl_runs
    DROP COLUMN IF EXISTS success_count,
    DROP COLUMN IF EXISTS failed_count,
    DROP COLUMN IF EXISTS new_urls_file_path;

COMMIT;

\echo Finished migration 001_drop_crawl_runs_derived_counts.sql
