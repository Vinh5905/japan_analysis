-- Loader-owned enrichment source. Idempotent for existing warehouses.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE TABLE IF NOT EXISTS raw.suumo_address_geocodes (
    provider TEXT NOT NULL,
    query_version TEXT NOT NULL,
    address_query TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    matched_address TEXT,
    coordinate_level TEXT,
    status TEXT NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_attempted_at TIMESTAMPTZ NOT NULL,
    next_retry_at TIMESTAMPTZ,
    error_message TEXT,
    raw_response JSONB,
    geocoded_at TIMESTAMPTZ,
    last_attempt_status TEXT NOT NULL,
    last_attempt_response JSONB,
    PRIMARY KEY (provider, query_version, address_query),
    CHECK (status IN ('matched', 'not_found', 'ambiguous', 'invalid_input', 'invalid_response', 'request_error')),
    CHECK (last_attempt_status IN ('matched', 'not_found', 'ambiguous', 'invalid_input', 'invalid_response', 'request_error')),
    CHECK (attempt_count >= 0),
    CHECK ((status = 'matched' AND latitude IS NOT NULL AND longitude IS NOT NULL
            AND latitude BETWEEN 20 AND 46 AND longitude BETWEEN 122 AND 154
            AND coordinate_level = 'chome' AND matched_address IS NOT NULL AND geocoded_at IS NOT NULL)
        OR (status <> 'matched' AND latitude IS NULL AND longitude IS NULL AND coordinate_level IS NULL))
);
