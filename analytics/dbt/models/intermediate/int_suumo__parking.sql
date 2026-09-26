-- Parking availability, location, capacity and fee share one source field.
with parsed as (
    select task_id, n_parking,
           case when n_parking = '付無料' or n_parking ~ '^付無料/(平置駐|屋内駐|機械式駐|屋根付駐|平置屋根付駐|シャッタ付屋内駐|リモコンシャッタ付駐|駐[23]台可)$'
                     or n_parking ~ '^(平置駐|屋内駐|機械式駐|屋根付駐|平置屋根付駐|シャッタ付屋内駐|リモコンシャッタ付駐|駐[23]台可)(/(平置駐|屋内駐|機械式駐|屋根付駐|平置屋根付駐|シャッタ付屋内駐|リモコンシャッタ付駐|駐[23]台可))?$'
                     or n_parking ~ '^(敷地内|近隣[0-9]+m)[0-9][0-9,]*円(/(平置駐|屋内駐|機械式駐|屋根付駐|平置屋根付駐|シャッタ付屋内駐|リモコンシャッタ付駐|駐[23]台可))*$'
                then true end as parking_listed
    from {{ ref('stg_suumo_parser_records') }}
)
select task_id, parking_listed,
       case when parking_listed then
            case when n_parking like '敷地内%' then 'onsite'
                 when n_parking like '近隣%' then 'nearby' else 'unspecified' end end as parking_location,
       case when parking_listed and n_parking like '近隣%'
            then (regexp_match(n_parking, '^近隣([0-9]+)m'))[1]::integer end as parking_distance_m,
       case when parking_listed and n_parking like '付無料%' then 0::bigint
            when parking_listed then {{ suumo_jpy("(regexp_match(n_parking, '([0-9][0-9,]*円)'))[1]") }} end as parking_fee_jpy,
       case when parking_listed then (regexp_match(n_parking,
            '(平置駐|屋内駐|機械式駐|屋根付駐|平置屋根付駐|シャッタ付屋内駐|リモコンシャッタ付駐)'))[1] end as parking_detail,
       case when parking_listed then (regexp_match(n_parking, '駐([23])台可'))[1]::integer end as parking_max_spaces
from parsed
