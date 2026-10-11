{{ config(materialized="mlit_stable_view") }}
with
    candidates as (
        select
            q.building_key,
            q.building_name_normalized as building_name,
            q.building_address_query as address_query,
            q.geography_key,
            l.latitude,
            l.longitude,
            l.status as location_status,
            l.coordinate_level,
            l.provider,
            l.google_place_id as place_id
        from {{ ref("int_suumo__building_lookup_candidates") }} q
        left join {{ ref("stg_suumo__building_locations") }} l using (building_key)
        where q.building_address_query like '大阪府大阪市%'
    )
select *, {{ mlit_location_fingerprint("candidates") }} as location_fingerprint
from candidates
