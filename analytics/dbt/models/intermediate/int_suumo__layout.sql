-- Main layout and component summary stay at one row per task.
with source as (
    select task_id, n_layout_detail as layout_detail_clean,
           case when upper(n_layout) = 'ワンルーム' then '1R'
                when upper(n_layout) ~ '^[1-9][0-9]*(R|K|DK|LK|LDK|SK|SDK|SLDK)$' then upper(n_layout) end as layout_normalized
    from {{ ref('stg_suumo_parser_records') }}
), tokens as (
    select s.task_id, token, token_order
    from source s
    cross join lateral regexp_split_to_table(
        regexp_replace(s.layout_detail_clean,
            '(洋|和|納戸|ロフト|LDK|DK|LD|K|L|D|S) +([0-9])', '\1\2', 'g'),
        ' +') with ordinality as t(token, token_order)
    where s.layout_detail_clean is not null
), components as (
    select t.task_id, t.token_order, m.parts[1] as label,
           case when t.token ~ '-[0-9]+(\.[0-9]+)?$' then null::numeric
                else nullif(m.parts[2], '')::numeric end as size_jo,
           m.match_order,
           m.parts[1] || coalesce(m.parts[2], '') as matched_text
    from tokens t
    cross join lateral regexp_matches(t.token,
        '(ロフト|納戸|LDK|DK|LD|洋|和|S|K|L|D)([0-9]+(\.[0-9]+)?)?', 'g')
        with ordinality as m(parts, match_order)
    where t.token !~ '^[0-9]'
), token_status as (
    select t.task_id, t.token_order,
           case when coalesce(string_agg(c.matched_text, '' order by c.match_order), '') = t.token
                then 0 else 1 end as failure_count
    from tokens t left join components c
      on t.task_id = c.task_id and t.token_order = c.token_order
    group by t.task_id, t.token_order, t.token
), summary as (
    select task_id,
           count(*)::integer as layout_space_count,
           count(*) filter (where label = '洋')::integer as western_room_count,
           count(*) filter (where label = '和')::integer as japanese_room_count,
           count(*) filter (where label in ('納戸', 'S'))::integer as service_room_count,
           max(size_jo) filter (where label in ('洋', '和')) as largest_private_room_jo,
           case when bool_or(label = 'LDK') then 'LDK'
                when bool_or(label = 'LD') and bool_or(label = 'K') then 'LD+K'
                when bool_or(label = 'DK') then 'DK'
                when bool_or(label = 'D') and bool_or(label = 'K') then 'D+K'
                when bool_or(label = 'K') then 'K' end as kitchen_type,
           case when bool_or(label = 'LDK') then sum(size_jo) filter (where label = 'LDK')
                when bool_or(label = 'LD') and bool_or(label = 'K') then sum(size_jo) filter (where label in ('LD', 'K'))
                when bool_or(label = 'DK') then sum(size_jo) filter (where label = 'DK')
                when bool_or(label = 'D') and bool_or(label = 'K') then sum(size_jo) filter (where label in ('D', 'K'))
                when bool_or(label = 'K') then sum(size_jo) filter (where label = 'K') end as kitchen_size_jo,
           bool_or(label = 'ロフト') as loft_present,
           max(size_jo) filter (where label = 'ロフト') as loft_size_jo
    from components group by task_id
), failures as (
    select task_id, sum(failure_count)::integer as layout_detail_parse_failure_count
    from token_status group by task_id
)
select s.task_id, s.layout_normalized,
       case when s.layout_normalized = '1R' then 1
            when s.layout_normalized is not null then (regexp_match(s.layout_normalized, '^([0-9]+)'))[1]::integer end as layout_room_count,
       case when s.layout_normalized is not null then position('S' in s.layout_normalized) > 0 end as layout_has_service_room,
       s.layout_detail_clean,
       case when s.layout_detail_clean is null then 'missing'
            when coalesce(x.layout_space_count, 0) = 0 then 'unparsed'
            when coalesce(f.layout_detail_parse_failure_count, 0) > 0 then 'partial'
            else 'full' end as layout_detail_parse_status,
       coalesce(f.layout_detail_parse_failure_count, 0) as layout_detail_parse_failure_count,
       (coalesce(f.layout_detail_parse_failure_count, 0) > 0) as flag_layout_detail_parse_failure,
       case when s.layout_detail_clean is not null then coalesce(x.layout_space_count, 0) end as layout_space_count,
       case when s.layout_detail_clean is not null then coalesce(x.western_room_count, 0) end as western_room_count,
       case when s.layout_detail_clean is not null then coalesce(x.japanese_room_count, 0) end as japanese_room_count,
       case when s.layout_detail_clean is not null then coalesce(x.service_room_count, 0) end as service_room_count,
       x.largest_private_room_jo, x.kitchen_type, x.kitchen_size_jo,
       case when s.layout_detail_clean is not null then coalesce(x.loft_present, false) end as loft_present,
       x.loft_size_jo
from source s left join summary x using (task_id) left join failures f using (task_id)
