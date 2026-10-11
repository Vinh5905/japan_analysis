{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
select
    dataset_key,
    zoning_area_key,
    min(source_effective_date) as source_effective_date,
    min(source_as_of_date) as source_as_of_date,
    jsonb_agg(
        jsonb_build_object(
            'file',
            source_file,
            'ordinal',
            feature_ordinal,
            'effective_date',
            source_effective_date
        )
        order by source_file, feature_ordinal
    ) as source_features
from {{ ref("int_mlit__polygon_states") }}
group by dataset_key, zoning_area_key
