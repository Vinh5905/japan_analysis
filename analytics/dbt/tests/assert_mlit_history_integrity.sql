{{ config(tags=["mlit_zoning_core"]) }}
select building_key
from {{ ref("bridge_building_zoning") }}
group by building_key
having count(*) filter(where is_current) <> 1
union all
select building_key
from {{ ref("bridge_building_zoning") }}
where valid_to_sequence <= valid_from_sequence
