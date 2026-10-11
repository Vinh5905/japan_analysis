{{ config(tags=["mlit_zoning_core"]) }}
with
    input as (
        select *
        from {{ source("zoning_operations", "zoning_run_inputs") }}
        where run_id = '{{ var("mlit_run_id", "") }}'
    ),
    output as (
        select *
        from {{ ref("int_mlit__zoning_matches") }}
        where run_id = '{{ var("mlit_run_id", "") }}'
    )
select coalesce(i.building_key, o.building_key) as building_key
from input i
full join output o using (run_id, building_key)
where
    i.building_key is null
    or o.building_key is null
    or (
        o.zoning_status = 'matched'
        and (
            o.polygon_count <> 1
            or o.boundary_distance_m is null
            or o.boundary_distance_m < 10
            or i.location_status is distinct from 'matched'
            or i.coordinate_level is distinct from 'building_poi'
            or i.latitude is null
            or i.longitude is null
            or i.latitude not between 20
            and 46
            or i.longitude not between 122
            and 154
        )
    )
    or (
        o.zoning_status <> 'matched'
        and (
            o.zoning_code is not null
            or o.zoning_name is not null
            or o.far_pct is not null
            or o.bcr_pct is not null
        )
    )
union all
select building_key
from output
group by building_key
having count(*) <> 1
