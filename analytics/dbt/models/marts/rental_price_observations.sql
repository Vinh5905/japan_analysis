{{ config(materialized="view") }}
-- Compute LAG over full history; consumers apply period filters afterwards.
with
    previous as (
        select
            f.*,
            d.source_id,
            d.suumo_property_code,
            lag(f.task_id) over w as previous_task_id,
            lag(f.rent_jpy) over w as previous_rent_jpy,
            lead(f.parsed_at_utc) over w as next_parsed_at_utc,
            lead(f.task_id) over w as next_task_id
        from {{ ref("fct_rental_price_observation") }} f
        join {{ ref("dim_rental_listing") }} d using (listing_version_key)
        window
            w as (
                partition by d.source_id, d.suumo_property_code
                order by f.parsed_at_utc, f.task_id
            )
    )
select
    p.task_id,
    p.record_origin,
    p.listing_version_key,
    p.geography_key,
    p.observation_quality_key,
    p.parsed_date_key,
    p.parsed_at_utc,
    p.rent_jpy,
    p.management_fee_jpy,
    p.deposit_jpy,
    p.key_money_jpy,
    p.guarantee_deposit_jpy,
    p.depreciation_jpy,
    p.brokerage_fee_amount_jpy,
    p.other_initial_costs_total_jpy,
    p.insurance_jpy,
    p.parking_fee_jpy,
    p.exclusive_area_m2,
    p.source_id,
    p.suumo_property_code,
    p.previous_task_id,
    p.previous_rent_jpy,
    p.next_parsed_at_utc,
    p.next_task_id,
    rent_jpy + management_fee_jpy as base_monthly_cost_jpy,
    case
        when exclusive_area_m2 > 0 then rent_jpy::numeric / exclusive_area_m2
    end as rent_per_m2_jpy,
    rent_jpy - previous_rent_jpy as rent_change_jpy,
    100.0
    * (rent_jpy - previous_rent_jpy)
    / nullif(previous_rent_jpy, 0) as rent_change_pct,
    next_task_id is null as is_latest_known,
    b.latitude,
    b.longitude,
    b.coordinate_level,
    b.geocode_status,
    b.geocode_provider,
    b.geocode_matched_address,
    b.geocoded_at,
    p.building_version_key,
    p.building_age_years,
    p.building_age_is_lower_bound,
    p.building_attributes_conflict,
    b.building_key,
    b.building_name,
    b.building_identity_status,
    l.room_number,
    b.building_type,
    b.structure,
    b.building_total_floors,
    b.total_units_count,
    b.built_at,
    b.built_at_precision,
    b.building_full_address_raw,
    b.building_full_address,
    b.postal_code,
    b.address_block,
    b.address_house_number,
    b.geocode_match_method,
    b.google_place_id,
    b.google_maps_url
from previous p
join {{ ref("dim_geography") }} g using (geography_key)

join {{ ref("dim_building") }} b using (building_version_key)
join {{ ref("dim_rental_listing") }} l using (listing_version_key)
