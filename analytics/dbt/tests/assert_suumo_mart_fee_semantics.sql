-- Sentinel fees must not become zero; explicit free values must remain zero.
with amounts as (
    select {{ suumo_mart_jpy("'未定'") }} as undecided,
           {{ suumo_mart_jpy("'-'") }} as missing,
           {{ suumo_mart_jpy("'なし'") }} as none,
           {{ suumo_mart_jpy("'不要'") }} as not_required,
           {{ suumo_mart_jpy("'1.25万円'") }} as quoted
)
select * from amounts where undecided is not null or missing is not null
   or none is distinct from 0::bigint or not_required is distinct from 0::bigint
   or quoted is distinct from 12500::bigint
