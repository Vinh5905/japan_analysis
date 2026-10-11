{{ config(indexes=[{"columns": ["observation_quality_key"], "unique": true}]) }}
select distinct
    observation_quality_key,
    (quality_attributes ->> 'flag_missing_core')::boolean as flag_missing_core,
    (quality_attributes ->> 'flag_floor_exceeds_building')::boolean
    as flag_floor_exceeds_building,
    (quality_attributes ->> 'flag_layout_detail_parse_failure')::boolean
    as flag_layout_detail_parse_failure,
    (quality_attributes ->> 'layout_detail_parse_status')::text
    as layout_detail_parse_status,
    (quality_attributes ->> 'station_access_parse_status')::text
    as station_access_parse_status
from {{ ref("int_suumo__mart_observations") }}
