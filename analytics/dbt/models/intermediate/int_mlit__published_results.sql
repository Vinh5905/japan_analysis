{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
-- Publication decisions never mutate the immutable spatial result.
select
    m.run_id,
    m.building_key,
    m.dataset_key,
    m.matching_version,
    m.location_fingerprint,
    case
        when a.accepted_null_buildings ? m.building_key
        then 'accepted_null'
        else m.zoning_status
    end as zoning_status,
    m.zoning_area_key,
    case
        when not (a.accepted_null_buildings ? m.building_key) then m.zoning_code
    end as zoning_code,
    case
        when not (a.accepted_null_buildings ? m.building_key) then m.zoning_name
    end as zoning_name,
    case
        when not (a.accepted_null_buildings ? m.building_key) then m.far_pct
    end as far_pct,
    case
        when not (a.accepted_null_buildings ? m.building_key) then m.bcr_pct
    end as bcr_pct,
    m.polygon_count,
    m.boundary_distance_m,
    m.candidate_areas,
    m.reason
from {{ ref("int_mlit__zoning_matches") }} m
join {{ source("zoning_operations", "zoning_runs") }} r using (run_id)
join
    {{ source("zoning_operations", "zoning_publication_audit") }} a
    on a.run_id = m.run_id
    and a.action = 'publish'
where r.publication_sequence is not null
