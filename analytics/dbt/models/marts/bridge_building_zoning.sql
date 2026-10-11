{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
with
    published as (
        select
            m.*,
            r.publication_sequence,
            r.published_at,
            {{ mlit_business_signature("m") }} as business_signature
        from {{ ref("int_mlit__published_results") }} m
        join {{ source("zoning_operations", "zoning_runs") }} r using (run_id)
        where r.publication_sequence is not null
    ),
    ordered as (
        select
            *,
            lag(business_signature) over (
                partition by building_key order by publication_sequence
            ) as previous_signature
        from published
    ),
    changes as (
        select *
        from ordered
        where business_signature is distinct from previous_signature
    ),
    versions as (
        select
            *,
            row_number() over (
                partition by building_key order by publication_sequence
            ) as version_number,
            lead(publication_sequence) over (
                partition by building_key order by publication_sequence
            ) as valid_to_sequence,
            lead(published_at) over (
                partition by building_key order by publication_sequence
            ) as valid_to
        from changes
    )
select
    building_key,
    md5(jsonb_build_array(building_key, run_id)::text) as building_zoning_version_key,
    version_number,
    publication_sequence as valid_from_sequence,
    valid_to_sequence,
    published_at as valid_from,
    valid_to,
    valid_to_sequence is null as is_current,
    zoning_status,
    zoning_code,
    zoning_name,
    far_pct,
    bcr_pct,
    zoning_area_key,
    run_id as starting_publication_run_id,
    business_signature
from versions
