{{ config(tags=["mlit_zoning_core"]) }}
with
    counts as (
        select
            d.dataset_key,
            d.feature_count,
            (
                select count(*)
                from {{ source("warehouse_raw", "mlit_zoning_polygons") }} p
                where p.dataset_key = d.dataset_key
            ) as raw_count,
            (
                select count(*)
                from {{ ref("int_mlit__polygon_states") }} p
                where p.dataset_key = d.dataset_key
            ) as normalized_count
        from {{ ref("stg_mlit__datasets") }} d
        where
            d.dataset_key
            = coalesce(nullif('{{ var("mlit_dataset_key", "") }}', ''), d.dataset_key)
    )
select dataset_key
from counts
where feature_count <> raw_count or raw_count <> normalized_count
