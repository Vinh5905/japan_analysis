-- Each meaningful source line must appear once; access_order is contiguous after
-- blank/sentinel lines.
with
    expected as (
        select s.task_id, count(*)::bigint as line_count
        from {{ ref("stg_suumo_parser_records") }} s
        cross join lateral regexp_split_to_table(s.station_access, '[\r\n]+') as t(line)
        where {{ suumo_clean("t.line") }} is not null
        group by s.task_id
    ),
    actual as (
        select
            task_id,
            count(*)::bigint as line_count,
            min(access_order) as first_order,
            max(access_order) as last_order
        from {{ ref("int_suumo__station_access") }}
        group by task_id
    )
select coalesce(e.task_id, a.task_id) as task_id
from expected e
full join actual a using (task_id)
where
    coalesce(e.line_count, 0) <> coalesce(a.line_count, 0)
    or (a.line_count > 0 and (a.first_order <> 1 or a.last_order <> a.line_count))
