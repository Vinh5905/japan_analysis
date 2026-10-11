-- Additive loader-owned audit source: safe for existing warehouse volumes.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.suumo_building_name_backfill (
    source_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    suumo_property_code TEXT,
    raw_snapshot_id BIGINT NOT NULL,
    storage_path TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    listing_headline_raw TEXT,
    building_name_raw TEXT,
    room_number_raw TEXT,
    building_name_source TEXT,
    building_name_parse_status TEXT NOT NULL,
    error_message TEXT,
    backfilled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source_id, task_id),
    CHECK (building_name_parse_status <> 'parsed' OR building_name_raw IS NOT NULL)
);
