{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
with
    raw as (
        select
            p.*,
            d.city_code,
            d.source_as_of_date,
            st_setsrid(st_geomfromgeojson(p.geometry::text), 6668) as geom,
            nullif(
                trim(normalize(p.properties ->> 'YoutoName', nfkc)), ''
            ) as zoning_name,
            nullif(
                trim(normalize(p.properties ->> 'YoutoCode', nfkc)), ''
            ) as zoning_code,
            {{ mlit_percent("p.properties->>'FAR'") }} as far_pct,
            {{ mlit_percent("p.properties->>'BCR'") }} as bcr_pct
        from {{ source("warehouse_raw", "mlit_zoning_polygons") }} p
        join {{ ref("stg_mlit__datasets") }} d using (dataset_key)
    )
select
    *,
    st_isvalid(geom)
    and not st_isempty(geom)
    and geometrytype(geom) in ('POLYGON', 'MULTIPOLYGON') as geometry_valid,
    case
        when
            (
                (nullif(trim(properties ->> 'FAR'), '') is not null and far_pct is null)
                or (
                    nullif(trim(properties ->> 'BCR'), '') is not null
                    and bcr_pct is null
                )
                or far_pct not between 0
                and 2000
                or bcr_pct not between 0
                and 100
            )
        then 'invalid_numeric'
        else 'valid'
    end as attribute_quality,
    case
        when properties ->> 'INDate' ~ '^\d{4}-\d{2}-\d{2}$'
        then (properties ->> 'INDate')::date
    end as source_effective_date
from raw
