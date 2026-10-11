{{ config(indexes=[{"columns": ["geography_key"], "unique": true}]) }}
with
    geographies as (
        select distinct
            geography_key,
            geography_attributes ->> 'prefecture' as prefecture,
            geography_attributes ->> 'district' as district,
            geography_attributes ->> 'municipality' as municipality,
            geography_attributes ->> 'ward' as ward,
            geography_attributes ->> 'locality' as locality,
            geography_attributes ->> 'chome' as chome
        from {{ ref("int_suumo__mart_observations") }}
    ),
    prepared as (
        select g.*, {{ suumo_geocode_address_query("g") }} as address_query
        from geographies g
    )
select
    g.geography_key,
    g.prefecture,
    g.district,
    g.municipality,
    g.ward,
    g.locality,
    g.chome,
    c.latitude,
    c.longitude,
    c.coordinate_level,
    coalesce(
        c.status,
        case when g.address_query is null then 'invalid_input' else 'not_requested' end
    ) as geocode_status,
    c.provider as geocode_provider,
    c.matched_address as geocode_matched_address,
    c.geocoded_at
from prepared g
left join {{ ref("stg_suumo__address_geocodes") }} c using (address_query)
