-- Exactly one active provider/policy row per candidate building; no dedupe
-- hides source corruption (source PK and dbt uniqueness enforce the grain).
select
    building_key,
    building_full_address_raw,
    building_full_address,
    postal_code,
    address_block,
    address_house_number,
    latitude::double precision as latitude,
    longitude::double precision as longitude,
    coordinate_level,
    status,
    provider,
    matched_address,
    match_method,
    google_place_id,
    google_maps_url,
    geocoded_at,
    query_version,
    address_query,
    search_query,
    attempt_count,
    request_count,
    last_attempted_at,
    next_retry_at,
    error_message,
    last_attempt_status
from {{ source("warehouse_raw", "suumo_building_locations") }}
where provider = 'google_maps_http' and query_version = 'building_name_chome_v1'
