-- The detail key is composite; parsed attributes must agree with parse_status.
with
    duplicate_keys as (
        select task_id, access_order
        from {{ ref("int_suumo__station_access") }}
        group by task_id, access_order
        having count(*) > 1
    ),
    invalid_rows as (
        select task_id, access_order
        from {{ ref("int_suumo__station_access") }}
        where
            (
                parse_status = 'parsed'
                and (
                    station_line is null
                    or station_name is null
                    or access_mode is null
                    or total_travel_minutes is null
                )
            )
            or (
                parse_status = 'unparsed'
                and (
                    station_line is not null
                    or station_name is not null
                    or access_mode is not null
                    or total_travel_minutes is not null
                )
            )
    )
select *
from duplicate_keys
union all
select *
from invalid_rows
