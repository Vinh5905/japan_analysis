{{ config(indexes=[{'columns': ['task_id'], 'unique': true},
                   {'columns': ['listing_version_key']}, {'columns': ['parsed_date_key']}]) }}
select o.task_id, o.record_origin,
       d.listing_version_key, g.geography_key, q.observation_quality_key,
       c.date_key as parsed_date_key, o.parsed_at_utc,
       o.rent_jpy,
       o.management_fee_jpy,
       o.deposit_jpy,
       o.key_money_jpy,
       o.guarantee_deposit_jpy,
       o.depreciation_jpy,
       o.brokerage_fee_amount_jpy,
       o.other_initial_costs_total_jpy,
       o.insurance_jpy,
       o.parking_fee_jpy,
       o.exclusive_area_m2
from {{ ref('int_suumo__mart_observations') }} o
join {{ ref('int_suumo__listing_timeline') }} t using (task_id)
join {{ ref('dim_rental_listing') }} d using (listing_version_key)
join {{ ref('dim_geography') }} g on o.geography_key = g.geography_key
join {{ ref('dim_observation_quality') }} q on o.observation_quality_key = q.observation_quality_key
join {{ ref('dim_date') }} c on c.calendar_date = (o.parsed_at_utc at time zone 'Asia/Tokyo')::date
