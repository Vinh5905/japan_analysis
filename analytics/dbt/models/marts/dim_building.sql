{{
    config(
        indexes=[
            {"columns": ["building_version_key"], "unique": true},
            {"columns": ["building_key", "version_number"], "unique": true},
        ]
    )
}}
-- Candidate building SCD2 plus latest-known location enrichment (not SCD2 attributes).
with
    versions as (
        select
            building_key,
            building_version_key,
            source_id,
            building_identity_status,
            building_name_normalized as building_name,
            geography_key,
            version_number,
            effective_from_utc,
            effective_from_observed_at_utc,
            effective_from_task_id,
            effective_to_utc,
            effective_to_observed_at_utc,
            effective_to_task_id,
            is_current,
            information_updated_at,
            building_event_time_basis,
            (building_attributes ->> 'building_type')::text as building_type,
            (building_attributes ->> 'structure')::text as structure,
            (building_attributes ->> 'building_total_floors')::integer
            as building_total_floors,
            (building_attributes ->> 'total_units_count')::integer as total_units_count,
            (building_attributes ->> 'built_at')::date as built_at,
            (building_attributes ->> 'built_at_precision')::text as built_at_precision
        from {{ ref("int_suumo__building_timeline") }}
        where task_id = effective_from_task_id
    )
select
    b.*,
    c.building_full_address_raw,
    c.building_full_address,
    c.postal_code,
    c.address_block,
    c.address_house_number,
    c.latitude,
    c.longitude,
    c.coordinate_level,
    coalesce(
        c.status,
        case when q.building_key is null then 'invalid_input' else 'not_requested' end
    ) as geocode_status,
    c.provider as geocode_provider,
    c.matched_address as geocode_matched_address,
    c.match_method as geocode_match_method,
    c.geocoded_at,
    c.google_place_id,
    c.google_maps_url
from versions b
left join {{ ref("int_suumo__building_lookup_candidates") }} q using (building_key)
left join {{ ref("stg_suumo__building_locations") }} c using (building_key)
