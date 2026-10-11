-- Debug: inspect the query/status/raw_response in the loader-owned cache.
select address_query
from {{ ref("stg_suumo__address_geocodes") }}
where
    (latitude is null) <> (longitude is null)
    or (
        status = 'matched'
        and (
            latitude is null
            or longitude is null
            or not (latitude between 20 and 46 and longitude between 122 and 154)
            or coordinate_level is distinct from 'chome'
            or matched_address is null
            or geocoded_at is null
        )
    )
    or (
        status <> 'matched'
        and (
            latitude is not null
            or longitude is not null
            or coordinate_level is not null
        )
    )
