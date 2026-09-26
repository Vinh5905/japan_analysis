-- Calendar dates and parse time; one row per parser task.
with parsed as (
    select task_id, n_built,
           case when parsed_at ~ '^\d{4}-\d{2}-\d{2}T' then parsed_at::timestamptz end as parsed_at_utc,
           case when information_updated_at_text ~ '^[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}$'
                     and to_char(to_date(information_updated_at_text, 'YYYY/MM/DD'), 'YYYY/MM/DD') = information_updated_at_text
                then to_date(information_updated_at_text, 'YYYY/MM/DD') end as information_updated_at,
           case when n_built ~ '^[0-9]{4}年([0-9]{1,2}月)?$'
                     and coalesce((regexp_match(n_built, '年([0-9]{1,2})月'))[1]::integer, 1) between 1 and 12
                then make_date((left(n_built, 4))::integer,
                    coalesce((regexp_match(n_built, '年([0-9]{1,2})月'))[1]::integer, 1), 1) end as built_at
    from {{ ref('stg_suumo_parser_records') }}
)
select task_id, parsed_at_utc, information_updated_at, built_at,
       case when built_at is not null then case when n_built ~ '月$' then 'month' else 'year' end end as built_at_precision
from parsed
