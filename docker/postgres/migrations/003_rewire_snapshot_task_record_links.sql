\echo Running migration 003_rewire_snapshot_task_record_links.sql

-- Raw snapshots no longer own source/run metadata directly. The crawl task is
-- the bridge between the fetched raw payload and the parsed output record.

BEGIN;

ALTER TABLE crawl_tasks
    ADD COLUMN IF NOT EXISTS record_id BIGINT;

DO $$
BEGIN
    IF to_regclass('parser_records') IS NOT NULL THEN
        UPDATE crawl_tasks AS ct
        SET record_id = selected_records.record_id
        FROM (
            SELECT DISTINCT ON (task_id)
                task_id,
                record_id
            FROM parser_records
            WHERE task_id IS NOT NULL
            ORDER BY task_id, parsed_at DESC, record_id DESC
        ) AS selected_records
        WHERE ct.task_id = selected_records.task_id
          AND ct.record_id IS NULL;
    END IF;
END $$;

DROP INDEX IF EXISTS idx_crawl_tasks_source_status;
DROP INDEX IF EXISTS idx_raw_snapshots_source_created_at;
DROP INDEX IF EXISTS idx_raw_snapshots_run;
DROP INDEX IF EXISTS idx_parser_records_source_record;
DROP INDEX IF EXISTS idx_parser_records_raw_snapshot;

ALTER TABLE raw_snapshots
    DROP COLUMN IF EXISTS source_id,
    DROP COLUMN IF EXISTS run_id;

ALTER TABLE crawl_tasks
    DROP COLUMN IF EXISTS source_id;

ALTER TABLE IF EXISTS parser_records
    DROP COLUMN IF EXISTS source_id,
    DROP COLUMN IF EXISTS raw_snapshot_id;

DO $$
BEGIN
    IF to_regclass('parser_records') IS NOT NULL THEN
        CREATE INDEX IF NOT EXISTS idx_parser_records_source_record_id
            ON parser_records (source_record_id);
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_crawl_tasks_record
    ON crawl_tasks (record_id)
    WHERE record_id IS NOT NULL;

DO $$
BEGIN
    IF to_regclass('parser_records') IS NOT NULL
       AND NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_crawl_tasks_record_id'
          AND conrelid = 'crawl_tasks'::regclass
    ) THEN
        ALTER TABLE crawl_tasks
            ADD CONSTRAINT fk_crawl_tasks_record_id
            FOREIGN KEY (record_id)
            REFERENCES parser_records (record_id);
    END IF;
END $$;

COMMIT;

\echo Finished migration 003_rewire_snapshot_task_record_links.sql
