{{ config(materialized="table") }}
-- Station access grain: one nonblank, nonsentinel source line per parser task.
-- Keep failed lines so parsing can be debugged without reading the parent history.
with
    source as (
        select task_id, batch_id, suumo_property_code, station_access
        from {{ ref("stg_suumo_parser_records") }}
    ),
    source_lines as (
        select
            s.task_id,
            s.batch_id,
            s.suumo_property_code,
            btrim(t.line) as raw_line,
            t.source_order
        from source s
        cross join lateral regexp_split_to_table(s.station_access, '[\r\n]+')
        with ordinality as t(line, source_order)
        where {{ suumo_clean("t.line") }} is not null
    ),
    lines as (
        select
            task_id,
            batch_id,
            suumo_property_code,
            raw_line,
            row_number() over (
                partition by task_id order by source_order
            ) as access_order,
            {{ suumo_norm("raw_line") }} as line
        from source_lines
    ),
    parsed as (
        select
            task_id,
            batch_id,
            suumo_property_code,
            access_order,
            raw_line,
            btrim(split_part(line, '/', 1)) as station_line,
            regexp_replace(
                btrim(
                    substring(
                        split_part(line, '/', 2)
                        from '^([^[:digit:]]*?)(?:バス|歩|車) *[0-9]+ *分'
                    )
                ),
                '駅$',
                ''
            ) as station_name,
            case
                when
                    position('バス' in split_part(line, '/', 1)) > 0
                    or line ~ 'バス *[0-9]+ *分'
                then 'bus'
                when line ~ '車 *[0-9]+ *分'
                then 'car'
                else 'walk'
            end as access_mode,
            (
                select sum((m.parts[2])::integer)
                from
                    regexp_matches(
                        split_part(line, '/', 2), '(バス|歩|車) *([0-9]+) *分', 'g'
                    ) as m(parts)
            ) as total_travel_minutes
        from lines
    ),
    classified as (
        select
            *,
            (
                station_line <> ''
                and coalesce(station_name, '') <> ''
                and total_travel_minutes is not null
            ) as is_parsed
        from parsed
    )
select
    task_id,
    batch_id,
    suumo_property_code,
    access_order,
    raw_line,
    case when is_parsed then 'parsed' else 'unparsed' end as parse_status,
    case when is_parsed then station_line end as station_line,
    case when is_parsed then station_name end as station_name,
    case when is_parsed then access_mode end as access_mode,
    case when is_parsed then total_travel_minutes::integer end as total_travel_minutes
from classified
