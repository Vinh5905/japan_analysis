{{
    config(
        materialized="incremental",
        incremental_strategy="append",
        full_refresh=false,
        post_hook="{{ mlit_immutable_results_hook() }}",
        tags=["mlit_zoning_core"],
        indexes=[{"columns": ["run_id", "building_key"], "unique": true}],
    )
}}
with
    inputs as (
        select
            i.*,
            r.dataset_key,
            r.matching_version,
            case
                when
                    i.location_status = 'matched'
                    and i.coordinate_level = 'building_poi'
                    and i.latitude between 20 and 46
                    and i.longitude between 122 and 154
                then
                    st_transform(
                        st_setsrid(st_makepoint(i.longitude, i.latitude), 4326), 6668
                    )
            end as point
        from {{ source("zoning_operations", "zoning_run_inputs") }} i
        join {{ source("zoning_operations", "zoning_runs") }} r using (run_id)
        where
            r.run_id = '{{ var("mlit_run_id", "") }}'
            {% if is_incremental() %}
                and not exists (
                    select 1 from {{ this }} old where old.run_id = i.run_id
                )
            {% endif %}
    ),
    polygons as (
        select distinct
            dataset_key,
            zoning_area_key,
            geom,
            zoning_code,
            zoning_name,
            far_pct,
            bcr_pct
        from {{ ref("int_mlit__polygon_states") }}
        where geometry_valid and attribute_quality = 'valid'
    ),
    spatial as (
        select
            i.run_id,
            i.building_key,
            i.dataset_key,
            i.matching_version,
            i.location_fingerprint,
            i.point,
            i.location_status,
            i.coordinate_level,
            count(p.zoning_area_key) as polygon_count,
            min(p.zoning_area_key) as sole_area_key,
            min(p.zoning_code) as candidate_zoning_code,
            min(p.zoning_name) as candidate_zoning_name,
            min(p.far_pct) as candidate_far_pct,
            min(p.bcr_pct) as candidate_bcr_pct,
            min(
                st_distance(
                    st_transform(i.point, 6674), st_boundary(st_transform(p.geom, 6674))
                )
            ) as boundary_distance_m,
            coalesce(
                jsonb_agg(
                    jsonb_build_object(
                        'area_key',
                        p.zoning_area_key,
                        'zoning_code',
                        p.zoning_code,
                        'zoning_name',
                        p.zoning_name,
                        'far_pct',
                        p.far_pct,
                        'bcr_pct',
                        p.bcr_pct
                    )
                )
                filter(where p.zoning_area_key is not null),
                '[]'::jsonb
            ) as candidate_areas
        from inputs i
        left join
            polygons p on p.dataset_key = i.dataset_key and st_covers(p.geom, i.point)
        group by
            i.run_id,
            i.building_key,
            i.dataset_key,
            i.matching_version,
            i.location_fingerprint,
            i.point,
            i.location_status,
            i.coordinate_level
    ),
    classified as (
        select
            *,
            case
                when point is null
                then 'no_valid_location'
                when polygon_count = 0
                then 'not_found'
                when polygon_count > 1
                then 'ambiguous'
                when boundary_distance_m < 10
                then 'near_boundary'
                else 'matched'
            end as zoning_status
        from spatial
    )
select
    run_id,
    building_key,
    dataset_key,
    matching_version,
    location_fingerprint,
    zoning_status,
    case when polygon_count = 1 then sole_area_key end as zoning_area_key,
    case when zoning_status = 'matched' then candidate_zoning_code end as zoning_code,
    case when zoning_status = 'matched' then candidate_zoning_name end as zoning_name,
    case when zoning_status = 'matched' then candidate_far_pct end as far_pct,
    case when zoning_status = 'matched' then candidate_bcr_pct end as bcr_pct,
    polygon_count,
    boundary_distance_m,
    candidate_areas,
    case
        zoning_status
        when 'near_boundary'
        then 'Distance to polygon boundary is below 10 metres'
        when 'ambiguous'
        then 'Multiple distinct normalized polygons cover point'
        when 'not_found'
        then 'No polygon covers point'
        when 'no_valid_location'
        then 'Requires matched building_poi coordinates within Japan'
    end as reason
from classified
