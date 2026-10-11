select source_id, task_id
from {{ source("warehouse_raw", "suumo_building_name_backfill") }}
group by source_id, task_id
having count(*) <> 1
union all
select source_id, task_id
from {{ source("warehouse_raw", "suumo_building_name_backfill") }}
where
    building_name_parse_status = 'parsed'
    and (
        building_name_raw is null
        or suumo_property_code is null
        or content_hash !~ '^[a-f0-9]{64}$'
    )
