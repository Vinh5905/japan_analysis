-- Metadata must never turn an unmatched/unresolved candidate into an area point.
select building_version_key
from {{ ref("dim_building") }}
where
    (latitude is null) <> (longitude is null)
    or (
        geocode_status = 'matched'
        and (
            latitude is null
            or longitude is null
            or latitude not between 20
            and 46
            or longitude not between 122
            and 154
            or coordinate_level is distinct from 'building_poi'
            or building_identity_status is distinct from 'named_candidate'
            or building_full_address is null
            or address_block is null
            or address_house_number is null
            or google_place_id is null
            or geocoded_at is null
            or geocode_provider is distinct from 'google_maps_http'
            or geocode_match_method is distinct from 'exact_name_chome_house_number'
        )
    )
    or (
        geocode_status <> 'matched'
        and (
            latitude is not null
            or longitude is not null
            or building_full_address is not null
            or google_place_id is not null
        )
    )
