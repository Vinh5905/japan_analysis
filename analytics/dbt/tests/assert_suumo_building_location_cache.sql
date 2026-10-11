select provider, query_version, building_key
from {{ source("warehouse_raw", "suumo_building_locations") }}
group by provider, query_version, building_key
having count(*) <> 1
