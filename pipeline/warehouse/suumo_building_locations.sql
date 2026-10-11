-- Loader-owned, idempotent enrichment source. Does not change source parser data.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.suumo_building_locations (
    provider TEXT NOT NULL,
    query_version TEXT NOT NULL,
    building_key TEXT NOT NULL,
    building_name_query TEXT,
    address_query TEXT,
    search_query TEXT,
    status TEXT NOT NULL,
    building_full_address_raw TEXT,
    building_full_address TEXT,
    postal_code TEXT,
    address_block TEXT,
    address_house_number TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    coordinate_level TEXT,
    matched_address TEXT,
    match_method TEXT,
    google_place_id TEXT,
    google_maps_url TEXT,
    geocoded_at TIMESTAMPTZ,
    raw_response JSONB,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    request_count INTEGER NOT NULL DEFAULT 0 CHECK (request_count >= 0),
    last_attempted_at TIMESTAMPTZ NOT NULL,
    next_retry_at TIMESTAMPTZ,
    error_message TEXT,
    last_attempt_status TEXT NOT NULL,
    last_attempt_response JSONB,
    PRIMARY KEY (provider, query_version, building_key),
    CHECK (
        status IN (
            'matched',
            'not_found',
            'ambiguous',
            'invalid_input',
            'invalid_response',
            'request_error',
            'blocked',
            'rate_limited'
        )
    ),
    CHECK (
        last_attempt_status IN (
            'matched',
            'not_found',
            'ambiguous',
            'invalid_input',
            'invalid_response',
            'request_error',
            'blocked',
            'rate_limited'
        )
    ),
    CHECK ((
        status = 'matched' AND latitude IS NOT NULL AND longitude IS NOT NULL
        AND latitude BETWEEN 20 AND 46 AND longitude BETWEEN 122 AND 154
        AND coordinate_level = 'building_poi' AND building_full_address IS NOT NULL
        AND address_block IS NOT NULL AND address_house_number IS NOT NULL
        AND google_place_id IS NOT NULL AND matched_address IS NOT NULL
        AND match_method IS NOT NULL AND geocoded_at IS NOT NULL
    )
    OR (
        status <> 'matched' AND latitude IS NULL AND longitude IS NULL
        AND coordinate_level IS NULL AND building_full_address IS NULL
        AND building_full_address_raw IS NULL AND postal_code IS NULL
        AND address_block IS NULL AND address_house_number IS NULL
        AND matched_address IS NULL AND match_method IS NULL
        AND google_place_id IS NULL AND google_maps_url IS NULL AND geocoded_at IS NULL
    ))
);
CREATE INDEX IF NOT EXISTS idx_suumo_building_locations_cooldown
ON raw.suumo_building_locations (provider, last_attempt_status, next_retry_at);
-- PostgreSQL CHECK accepts UNKNOWN: explicitly forbid a NULL matched level.
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
        WHERE conrelid = 'raw.suumo_building_locations'::regclass
          AND conname = 'suumo_building_locations_matched_metadata') THEN
        ALTER TABLE raw.suumo_building_locations
            ADD CONSTRAINT suumo_building_locations_matched_metadata CHECK
            (status <> 'matched' OR (coordinate_level IS NOT NULL
             AND building_full_address_raw IS NOT NULL));
    END IF;
END $$;
