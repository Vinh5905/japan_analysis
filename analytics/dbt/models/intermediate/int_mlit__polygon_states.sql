{{
    config(
        materialized="incremental",
        incremental_strategy="append",
        full_refresh=false,
        tags=["mlit_zoning_core"],
        indexes=[
            {"columns": ["geom"], "type": "gist"},
            {
                "columns": ["dataset_key", "source_file", "feature_ordinal"],
                "unique": true,
            },
        ],
    )
}}
select
    *,
    md5(
        jsonb_build_array(
            city_code,
            encode(st_asewkb(st_normalize(geom)), 'hex'),
            zoning_code,
            zoning_name,
            far_pct,
            bcr_pct
        )::text
    ) as zoning_area_key
from {{ ref("stg_mlit__zoning_polygons") }} p
{% if is_incremental() %}
    where
        not exists (
            select 1
            from {{ this }} old
            where
                old.dataset_key = p.dataset_key
                and old.source_file = p.source_file
                and old.feature_ordinal = p.feature_ordinal
        )
{% endif %}
