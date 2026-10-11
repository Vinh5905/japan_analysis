{{ config(indexes=[{"columns": ["station_label_key"], "unique": true}]) }}
select distinct
    md5(
        jsonb_build_array(o.source_id, s.station_line, s.station_name)::text
    ) as station_label_key,
    o.source_id,
    s.station_line,
    s.station_name
from {{ ref("int_suumo__station_access") }} s
join {{ ref("int_suumo__mart_observations") }} o using (task_id)
where s.parse_status = 'parsed'
union all
select '00000000000000000000000000000000', null::bigint, null::text, null::text
