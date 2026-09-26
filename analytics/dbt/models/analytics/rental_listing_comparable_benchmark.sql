-- Group 2: benchmark every latest listing against the first peer tier with at
-- least five known rents. The listing itself remains in its peer population.
with listings as (
    select * from {{ ref('rental_listing_latest') }}
), tier_1 as (
    select prefecture, municipality, ward, locality, layout_normalized,
           area_band, building_type,
           count(rent_jpy)::bigint as sample_size,
           count(rent_per_m2_jpy)::bigint as rent_per_m2_sample_size,
           percentile_cont(0.5) within group (order by rent_jpy)
               filter (where rent_jpy is not null) as median_rent_jpy,
           percentile_cont(0.5) within group (order by rent_per_m2_jpy)
               filter (where rent_per_m2_jpy is not null) as median_rent_per_m2_jpy
    from listings
    group by prefecture, municipality, ward, locality, layout_normalized,
             area_band, building_type
), tier_2 as (
    select prefecture, municipality, ward, layout_normalized, area_band,
           building_type,
           count(rent_jpy)::bigint as sample_size,
           count(rent_per_m2_jpy)::bigint as rent_per_m2_sample_size,
           percentile_cont(0.5) within group (order by rent_jpy)
               filter (where rent_jpy is not null) as median_rent_jpy,
           percentile_cont(0.5) within group (order by rent_per_m2_jpy)
               filter (where rent_per_m2_jpy is not null) as median_rent_per_m2_jpy
    from listings
    group by prefecture, municipality, ward, layout_normalized, area_band,
             building_type
), tier_3 as (
    select prefecture, municipality, ward, layout_normalized, area_band,
           count(rent_jpy)::bigint as sample_size,
           count(rent_per_m2_jpy)::bigint as rent_per_m2_sample_size,
           percentile_cont(0.5) within group (order by rent_jpy)
               filter (where rent_jpy is not null) as median_rent_jpy,
           percentile_cont(0.5) within group (order by rent_per_m2_jpy)
               filter (where rent_per_m2_jpy is not null) as median_rent_per_m2_jpy
    from listings
    group by prefecture, municipality, ward, layout_normalized, area_band
), selected as (
    select
        l.*,
        case when t1.sample_size >= 5 then 'locality_layout_area_building'
             when t2.sample_size >= 5 then 'ward_layout_area_building'
             when t3.sample_size >= 5 then 'ward_layout_area'
             else 'insufficient_sample' end as benchmark_tier,
        case when t1.sample_size >= 5 then t1.sample_size
             when t2.sample_size >= 5 then t2.sample_size
             when t3.sample_size >= 5 then t3.sample_size end as peer_sample_size,
        case when t1.sample_size >= 5 then t1.rent_per_m2_sample_size
             when t2.sample_size >= 5 then t2.rent_per_m2_sample_size
             when t3.sample_size >= 5 then t3.rent_per_m2_sample_size end
             as peer_rent_per_m2_sample_size,
        case when t1.sample_size >= 5 then t1.median_rent_jpy
             when t2.sample_size >= 5 then t2.median_rent_jpy
             when t3.sample_size >= 5 then t3.median_rent_jpy end as peer_median_rent_jpy,
        case when t1.sample_size >= 5 then t1.median_rent_per_m2_jpy
             when t2.sample_size >= 5 then t2.median_rent_per_m2_jpy
             when t3.sample_size >= 5 then t3.median_rent_per_m2_jpy end
             as peer_median_rent_per_m2_jpy
    from listings l
    left join tier_1 t1
      on t1.prefecture is not distinct from l.prefecture
     and t1.municipality is not distinct from l.municipality
     and t1.ward is not distinct from l.ward
     and t1.locality is not distinct from l.locality
     and t1.layout_normalized is not distinct from l.layout_normalized
     and t1.area_band is not distinct from l.area_band
     and t1.building_type is not distinct from l.building_type
    left join tier_2 t2
      on t2.prefecture is not distinct from l.prefecture
     and t2.municipality is not distinct from l.municipality
     and t2.ward is not distinct from l.ward
     and t2.layout_normalized is not distinct from l.layout_normalized
     and t2.area_band is not distinct from l.area_band
     and t2.building_type is not distinct from l.building_type
    left join tier_3 t3
      on t3.prefecture is not distinct from l.prefecture
     and t3.municipality is not distinct from l.municipality
     and t3.ward is not distinct from l.ward
     and t3.layout_normalized is not distinct from l.layout_normalized
     and t3.area_band is not distinct from l.area_band
)
select
    *,
    rent_jpy - peer_median_rent_jpy as rent_vs_peer_median_jpy,
    100.0 * (rent_jpy - peer_median_rent_jpy)
        / nullif(peer_median_rent_jpy, 0) as rent_vs_peer_median_pct,
    rent_per_m2_jpy - peer_median_rent_per_m2_jpy
        as rent_per_m2_vs_peer_median_jpy,
    100.0 * (rent_per_m2_jpy - peer_median_rent_per_m2_jpy)
        / nullif(peer_median_rent_per_m2_jpy, 0)
        as rent_per_m2_vs_peer_median_pct,
    case
        when peer_median_rent_jpy is null or rent_jpy is null then 'not_scored'
        when 100.0 * (rent_jpy - peer_median_rent_jpy)
             / nullif(peer_median_rent_jpy, 0) <= -10 then 'below_peer_median_10pct'
        when 100.0 * (rent_jpy - peer_median_rent_jpy)
             / nullif(peer_median_rent_jpy, 0) >= 10 then 'above_peer_median_10pct'
        else 'within_10pct_of_peer_median'
    end as rent_position
from selected
