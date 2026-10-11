-- Listing payments and insurance charges. Parking charges belong to parking.
with
    parsed as (
        select
            task_id,
            n_insurance,
            {{ suumo_jpy("rent_price_text") }} as rent_jpy,
            {{ suumo_jpy("management_fee_text", true) }} as management_fee_jpy,
            {{ suumo_jpy("deposit_text", true) }} as deposit_jpy,
            {{ suumo_jpy("key_money_text", true) }} as key_money_jpy,
            {{ suumo_jpy("guarantee_deposit_text", true) }} as guarantee_deposit_jpy,
            {{ suumo_jpy("depreciation_text", true) }} as depreciation_jpy,
            {{ suumo_jpy("brokerage_fee", true) }} as brokerage_fee_jpy,
            case
                when
                    {{ suumo_norm("brokerage_fee") }}
                    ~ '^[0-9]+(\.[0-9]+)? *(ヶ|ヵ|か|ケ)月$'
                then
                    (
                        regexp_match(
                            {{ suumo_norm("brokerage_fee") }}, '^([0-9]+(\.[0-9]+)?)'
                        )
                    )[1]::numeric
            end as brokerage_fee_months,
            case
                when
                    {{ suumo_norm("other_initial_costs") }}
                    ~ '^合計[0-9]+(\.[0-9]+)?万円(\(内訳:.*\))?$'
                then
                    {{
                        suumo_jpy(
                            "regexp_replace(split_part("
                            ~ suumo_norm("other_initial_costs")
                            ~ ", '万円', 1), '^合計', '') || '万円'"
                        )
                    }}
            end as other_initial_costs_total_jpy,
            case
                when n_insurance = '不要'
                then false
                when n_insurance = '要'
                then true
                when
                    n_insurance ~ '^[0-9][0-9,]*(\.[0-9]+)? *(万円|円) *([0-9]+年)?$'
                    and {{ suumo_jpy("regexp_replace(n_insurance, ' *[0-9]+年$', '')") }}
                    > 0
                    and coalesce(
                        (regexp_match(n_insurance, '([0-9]+)年$'))[1]::integer, 1
                    )
                    > 0
                then true
            end as insurance_required
        from {{ ref("stg_suumo_parser_records") }}
    )
select
    task_id,
    rent_jpy,
    management_fee_jpy,
    deposit_jpy,
    key_money_jpy,
    guarantee_deposit_jpy,
    depreciation_jpy,
    brokerage_fee_jpy,
    brokerage_fee_months,
    coalesce(
        brokerage_fee_jpy, round(brokerage_fee_months * rent_jpy)::bigint
    ) as brokerage_fee_estimated_jpy,
    other_initial_costs_total_jpy,
    insurance_required,
    case
        when insurance_required and n_insurance <> '要'
        then {{ suumo_jpy("regexp_replace(n_insurance, ' *[0-9]+年$', '')") }}
    end as insurance_jpy,
    case
        when insurance_required and n_insurance <> '要'
        then (regexp_match(n_insurance, '([0-9]+)年$'))[1]::integer
    end as insurance_period_years,
    (rent_jpy + management_fee_jpy)::bigint as base_monthly_cost_jpy
from parsed
