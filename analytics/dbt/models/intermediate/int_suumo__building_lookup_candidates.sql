{{
    config(
        materialized="table", indexes=[{"columns": ["building_key"], "unique": true}]
    )
}}
-- Input side of the HTTP gate. Never reads the location cache.
select distinct
    building_key,
    source_id,
    geography_key,
    building_name_normalized,
    building_address_query
from {{ ref("int_suumo__building_events") }}
where
    building_identity_status = 'named_candidate'
    and building_name_normalized is not null
    and building_address_query is not null
