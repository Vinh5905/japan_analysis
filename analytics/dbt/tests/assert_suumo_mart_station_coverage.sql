with expected as (
    select s.task_id, s.access_order, s.parse_status, s.access_mode, s.total_travel_minutes
    from {{ ref('int_suumo__station_access') }} s
    join {{ ref('fct_rental_price_observation') }} f using (task_id)
), actual as (
    select task_id, access_order, parse_status, access_mode, total_travel_minutes
    from {{ ref('bridge_observation_station_access') }}
)
(select * from expected except all select * from actual)
union all
(select * from actual except all select * from expected)
