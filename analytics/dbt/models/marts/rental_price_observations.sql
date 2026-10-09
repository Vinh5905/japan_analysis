{{ config(materialized='view') }}
-- Compute LAG over full history; consumers apply period filters afterwards.
with previous as (
    select f.*, d.source_id, d.suumo_property_code,
           lag(f.task_id) over w as previous_task_id,
           lag(f.rent_jpy) over w as previous_rent_jpy,
           lead(f.parsed_at_utc) over w as next_parsed_at_utc,
           lead(f.task_id) over w as next_task_id
    from {{ ref('fct_rental_price_observation') }} f
    join {{ ref('dim_rental_listing') }} d using (listing_version_key)
    window w as (partition by d.source_id, d.suumo_property_code
                 order by f.parsed_at_utc, f.task_id)
)
select p.*, rent_jpy + management_fee_jpy as base_monthly_cost_jpy,
       case when exclusive_area_m2 > 0 then rent_jpy::numeric / exclusive_area_m2 end as rent_per_m2_jpy,
       rent_jpy - previous_rent_jpy as rent_change_jpy,
       100.0 * (rent_jpy - previous_rent_jpy) / nullif(previous_rent_jpy, 0) as rent_change_pct,
       next_task_id is null as is_latest_known,
       g.latitude, g.longitude, g.coordinate_level, g.geocode_status,
       g.geocode_provider, g.geocode_matched_address, g.geocoded_at
from previous p
join {{ ref('dim_geography') }} g using (geography_key)
