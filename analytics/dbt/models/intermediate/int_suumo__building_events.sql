{{ config(materialized="table", indexes=[{"columns": ["task_id"], "unique": true}]) }}
-- One candidate identity/event per eligible observation; names never flow backwards.
with
    addressed as (
        select o.*, {{ suumo_geocode_address_query("g") }} as building_address_query
        from {{ ref("int_suumo__mart_observations") }} o
        cross join
            lateral(
                select
                    geography_attributes ->> 'prefecture' as prefecture,
                    geography_attributes ->> 'district' as district,
                    geography_attributes ->> 'municipality' as municipality,
                    geography_attributes ->> 'ward' as ward,
                    geography_attributes ->> 'locality' as locality,
                    geography_attributes ->> 'chome' as chome
            ) g
    )
select
    task_id,
    source_id,
    suumo_property_code,
    parsed_at_utc,
    information_updated_at,
    geography_key,
    building_name_normalized,
    building_address_query,
    building_attributes
    || jsonb_build_object('geography_key', geography_key) as building_attributes,
    {{
        suumo_building_key(
            "source_id",
            "suumo_property_code",
            "geography_key",
            "building_name_normalized",
            "building_address_query",
        )
    }} as building_key,
    case
        when building_name_normalized is not null and building_address_query is not null
        then 'named_candidate'
        else 'unresolved_listing'
    end as building_identity_status
from addressed
