{{ config(tags=["mlit_zoning_core"]) }}
select *
from {{ ref("int_mlit__polygon_states") }}
where
    dataset_key = coalesce(nullif('{{ var("mlit_dataset_key", "") }}', ''), dataset_key)
    and (
        not geometry_valid
        or attribute_quality <> 'valid'
        or zoning_code is null
        or zoning_name is null
    )
