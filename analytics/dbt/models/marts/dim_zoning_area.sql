{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
-- Identical normalized polygon/business content reuses its key across releases.
select distinct
    zoning_area_key,
    city_code,
    st_normalize(geom) as geom,
    zoning_code,
    zoning_name,
    far_pct,
    bcr_pct
from {{ ref("int_mlit__polygon_states") }}
where geometry_valid and attribute_quality = 'valid'
