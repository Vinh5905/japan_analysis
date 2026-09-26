-- Move-in and tenancy terms; date-like move-in values stay with contract semantics.
with parsed as (
    select task_id, n_move_in, n_contract,
           case when n_move_in = '即' then 'immediate'
                when n_move_in = '相談' then 'consultation'
                when n_move_in ~ '^[`''’‘]?[[:space:]]*[0-9]{2,4}年[[:space:]]*[0-9]{1,2}月[[:space:]]*(上旬|初旬|中旬|下旬)?$'
                     and (regexp_match(n_move_in, '([0-9]{1,2})月'))[1]::int between 1 and 12 then 'scheduled'
                else 'unknown' end as move_in_status,
           case when n_contract ~ '^(普通借家|定期借家) *([0-9]+ *年)? *([0-9]+ *(ヶ|か|ケ)?月)?$'
                     and n_contract ~ '[0-9]+ *(年|ヶ?月|か月|ケ月)'
                then case when n_contract like '普通借家%' then 'ordinary' else 'fixed_term' end end as contract_type
    from {{ ref('stg_suumo_parser_records') }}
)
select task_id, move_in_status,
       case when move_in_status = 'scheduled' then
            lpad((case when length((regexp_match(n_move_in, '([0-9]{2,4})年'))[1]) = 2
                       then 2000 + (regexp_match(n_move_in, '([0-9]{2,4})年'))[1]::integer
                       else (regexp_match(n_move_in, '([0-9]{2,4})年'))[1]::integer end)::text, 4, '0')
            || '-' || lpad((regexp_match(n_move_in, '([0-9]{1,2})月'))[1], 2, '0') end as move_in_month,
       case when move_in_status = 'scheduled' then
            case (regexp_match(n_move_in, '(上旬|初旬|中旬|下旬)$'))[1]
                 when '上旬' then 'early' when '初旬' then 'early'
                 when '中旬' then 'middle' when '下旬' then 'late' end end as move_in_period,
       contract_type,
       case when contract_type is not null then coalesce((regexp_match(n_contract, '([0-9]+) *年'))[1]::integer, 0) end as contract_years,
       case when contract_type is not null then coalesce((regexp_match(n_contract, '([0-9]+) *(ヶ|か|ケ)?月'))[1]::integer, 0) end as contract_months
from parsed
