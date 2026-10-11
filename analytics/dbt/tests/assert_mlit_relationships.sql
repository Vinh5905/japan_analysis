{{ config(tags=["mlit_zoning_core"]) }}
-- Audit and presentation keys must refer to the same immutable run/scope.
select 'match_run_input' as violation, m.run_id as entity_key
from {{ ref("int_mlit__zoning_matches") }} m
left join
    {{ source("zoning_operations", "zoning_run_inputs") }} i using (
        run_id, building_key
    )
left join {{ source("zoning_operations", "zoning_runs") }} r using (run_id)
where i.building_key is null or r.run_id is null or m.dataset_key <> r.dataset_key
union all
select 'match_area', m.run_id
from {{ ref("int_mlit__zoning_matches") }} m
left join {{ ref("int_mlit__dataset_areas") }} a using (dataset_key, zoning_area_key)
where m.zoning_area_key is not null and a.zoning_area_key is null
union all
select 'dataset_area', a.dataset_key
from {{ ref("int_mlit__dataset_areas") }} a
left join {{ ref("stg_mlit__datasets") }} d using (dataset_key)
left join {{ ref("dim_zoning_area") }} z using (zoning_area_key)
where d.dataset_key is null or z.zoning_area_key is null
union all
select 'bridge_publication', b.building_zoning_version_key
from {{ ref("bridge_building_zoning") }} b
left join
    {{ source("zoning_operations", "zoning_runs") }} r
    on r.run_id = b.starting_publication_run_id
where r.publication_sequence is null or r.publication_sequence <> b.valid_from_sequence
union all
select 'active_publication', p.run_id
from {{ source("zoning_operations", "zoning_publication_pointer") }} p
left join {{ source("zoning_operations", "zoning_runs") }} r using (run_id)
where r.publication_sequence is null or r.city_code <> p.city_code
