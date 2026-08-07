-- Keep only loader outcome counts that are used by the warehouse ingestion flow.
-- inserted_count means records accepted into warehouse; failed_count means
-- parser records rejected by validation or failed during row write.

ALTER TABLE load_batches
    DROP COLUMN IF EXISTS updated_count,
    DROP COLUMN IF EXISTS skipped_count;
