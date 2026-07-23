\echo Running migration 006_replace_parser_records_with_load_batches.sql

-- Parser records are JSON objects inside compressed load batch files, not a
-- PostgreSQL table. crawl_tasks now points to the load batch that contains the
-- parser record for that task.

BEGIN;

ALTER TABLE crawl_tasks
    DROP CONSTRAINT IF EXISTS fk_crawl_tasks_record_id;

DROP INDEX IF EXISTS idx_crawl_tasks_record;

ALTER TABLE crawl_tasks
    DROP COLUMN IF EXISTS record_id,
    ADD COLUMN IF NOT EXISTS batch_id BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_crawl_tasks_batch_id'
          AND conrelid = 'crawl_tasks'::regclass
    ) THEN
        ALTER TABLE crawl_tasks
            ADD CONSTRAINT fk_crawl_tasks_batch_id
            FOREIGN KEY (batch_id)
            REFERENCES load_batches (batch_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_crawl_tasks_batch
    ON crawl_tasks (batch_id)
    WHERE batch_id IS NOT NULL;

DROP INDEX IF EXISTS idx_parser_records_source_record_id;
DROP INDEX IF EXISTS idx_parser_records_task;
DROP INDEX IF EXISTS idx_parser_records_data_hash;
DROP INDEX IF EXISTS idx_parser_records_valid;

DROP TABLE IF EXISTS parser_records CASCADE;

COMMIT;

\echo Finished migration 006_replace_parser_records_with_load_batches.sql
