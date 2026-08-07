with ranked as (
    select
        *,
        row_number() over (
            partition by coalesce(suumo_property_code, task_id::text)
            order by loaded_at desc, task_id desc
        ) as record_rank
    from {{ ref('stg_suumo_rentals') }}
)

select
    task_id,
    batch_id,
    source_id,
    data_hash,
    loaded_at,
    image_public_url,
    image_storage_path,
    rent_price_text,
    deposit_text,
    management_fee_text,
    key_money_text,
    guarantee_deposit_text,
    depreciation_text,
    phone_number,
    address,
    station_access,
    layout,
    exclusive_area_text,
    building_age_text,
    floor_text,
    direction,
    building_type,
    layout_detail,
    structure,
    building_floors,
    built_at_text,
    energy_efficiency,
    insulation_performance,
    estimated_utility_cost,
    insurance,
    parking,
    move_in,
    conditions,
    suumo_property_code,
    information_updated_at_text,
    contract_period,
    brokerage_fee,
    guarantee_company,
    other_initial_costs,
    other_monthly_costs,
    transaction_type,
    shop_property_code,
    total_units,
    next_update_date_text,
    remarks
from ranked
where record_rank = 1
