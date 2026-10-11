-- One row per query for the active provider/policy; the loader owns this source.
select
    address_query,
    latitude::double precision as latitude,
    longitude::double precision as longitude,
    matched_address,
    coordinate_level,
    status,
    provider,
    query_version,
    geocoded_at,
    last_attempted_at,
    next_retry_at,
    error_message,
    attempt_count
from {{ source("warehouse_raw", "suumo_address_geocodes") }}
where provider = 'gsi_address_search' and query_version = 'chome_v1'
