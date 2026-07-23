\echo Running migration 002_seed_suumo_crawl_source.sql

-- Keep the default SUUMO source aligned with the current schema contract.
-- SUUMO is pinned to source_id = 1 because several metadata tables default to
-- source_id = 1 while the project only has this source configured.

BEGIN;

ALTER TABLE crawl_sources
    ALTER COLUMN robots_policy SET DEFAULT 'allowed';

INSERT INTO crawl_sources (
    source_id,
    source_key,
    source_name,
    base_url,
    crawl_frequency,
    is_active,
    robots_policy,
    notes
)
VALUES (
    1,
    'suumo',
    'SUUMO',
    'https://suumo.jp',
    'schedule',
    TRUE,
    'allowed',
    NULL
)
ON CONFLICT (source_id) DO UPDATE
SET
    source_key = EXCLUDED.source_key,
    source_name = EXCLUDED.source_name,
    base_url = EXCLUDED.base_url,
    crawl_frequency = EXCLUDED.crawl_frequency,
    is_active = EXCLUDED.is_active,
    robots_policy = EXCLUDED.robots_policy,
    notes = EXCLUDED.notes,
    updated_at = now();

SELECT setval(
    pg_get_serial_sequence('crawl_sources', 'source_id'),
    COALESCE((SELECT MAX(source_id) FROM crawl_sources), 1),
    true
);

COMMIT;

\echo Finished migration 002_seed_suumo_crawl_source.sql
