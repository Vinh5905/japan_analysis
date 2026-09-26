-- Group 3: descriptive association between a listing feature and asking
-- price, while holding locality, layout and area band constant.
with listings as (
    select * from {{ ref('rental_listing_latest') }}
), strata as (
    select prefecture, municipality, ward, locality, layout_normalized, area_band,
           count(rent_jpy)::bigint as stratum_rent_sample_size,
           count(rent_per_m2_jpy)::bigint as stratum_rent_per_m2_sample_size,
           percentile_cont(0.5) within group (order by rent_jpy)
               filter (where rent_jpy is not null) as stratum_median_rent_jpy,
           percentile_cont(0.5) within group (order by rent_per_m2_jpy)
               filter (where rent_per_m2_jpy is not null)
               as stratum_median_rent_per_m2_jpy
    from listings
    group by prefecture, municipality, ward, locality, layout_normalized, area_band
), expanded as (
    select
        l.prefecture, l.municipality, l.ward, l.locality,
        l.layout_normalized, l.area_band, l.area_band_sort,
        l.rent_jpy, l.rent_per_m2_jpy,
        f.feature_name, f.feature_value, f.feature_sort,
        f.feature_value <> 'Unknown' as is_known_feature
    from listings l
    cross join lateral (values
        ('building_age_band',
         case when l.building_age_is_lower_bound then '99+ (lower bound)'
              when l.building_age_years is null then 'Unknown'
              when l.building_age_years <= 5 then '0-5'
              when l.building_age_years <= 10 then '6-10'
              when l.building_age_years <= 20 then '11-20'
              when l.building_age_years <= 30 then '21-30'
              else '31+' end,
         case when l.building_age_is_lower_bound then 6
              when l.building_age_years is null then 0
              when l.building_age_years <= 5 then 1
              when l.building_age_years <= 10 then 2
              when l.building_age_years <= 20 then 3
              when l.building_age_years <= 30 then 4 else 5 end),
        ('floor_band',
         case when l.floor_number is null and l.floor_min is not null then 'Range/multiple'
              when l.floor_number is null then 'Unknown'
              when l.floor_number <= 0 then 'Basement/ground'
              when l.floor_number = 1 then '1'
              when l.floor_number <= 3 then '2-3'
              when l.floor_number <= 5 then '4-5'
              when l.floor_number <= 10 then '6-10' else '11+' end,
         case when l.floor_number is null and l.floor_min is not null then 7
              when l.floor_number is null then 0
              when l.floor_number <= 0 then 1
              when l.floor_number = 1 then 2
              when l.floor_number <= 3 then 3
              when l.floor_number <= 5 then 4
              when l.floor_number <= 10 then 5 else 6 end),
        ('direction', coalesce(l.direction, 'Unknown'), 0),
        ('structure', coalesce(l.structure, 'Unknown'), 0),
        ('building_type', coalesce(l.building_type, 'Unknown'), 0)
    ) f(feature_name, feature_value, feature_sort)
), feature_groups as (
    select
        prefecture, municipality, ward, locality, layout_normalized,
        area_band, min(area_band_sort) as area_band_sort,
        feature_name, feature_value, feature_sort, is_known_feature,
        count(*)::bigint as listing_count,
        count(rent_jpy)::bigint as rent_sample_size,
        count(rent_per_m2_jpy)::bigint as rent_per_m2_sample_size,
        percentile_cont(0.25) within group (order by rent_jpy)
            filter (where rent_jpy is not null) as rent_p25_jpy,
        percentile_cont(0.5) within group (order by rent_jpy)
            filter (where rent_jpy is not null) as rent_median_jpy,
        percentile_cont(0.75) within group (order by rent_jpy)
            filter (where rent_jpy is not null) as rent_p75_jpy,
        percentile_cont(0.5) within group (order by rent_per_m2_jpy)
            filter (where rent_per_m2_jpy is not null) as rent_per_m2_median_jpy
    from expanded
    group by prefecture, municipality, ward, locality, layout_normalized,
             area_band, feature_name, feature_value, feature_sort, is_known_feature
)
select
    md5(jsonb_build_array(
        f.prefecture, f.municipality, f.ward, f.locality,
        f.layout_normalized, f.area_band, f.feature_name, f.feature_value
    )::text) as feature_segment_key,
    f.*,
    s.stratum_rent_sample_size,
    s.stratum_rent_per_m2_sample_size,
    s.stratum_median_rent_jpy,
    s.stratum_median_rent_per_m2_jpy,
    100.0 * (f.rent_median_jpy - s.stratum_median_rent_jpy)
        / nullif(s.stratum_median_rent_jpy, 0) as rent_premium_vs_stratum_pct,
    100.0 * (f.rent_per_m2_median_jpy - s.stratum_median_rent_per_m2_jpy)
        / nullif(s.stratum_median_rent_per_m2_jpy, 0)
        as rent_per_m2_premium_vs_stratum_pct,
    (f.is_known_feature and f.rent_sample_size >= 5
     and s.stratum_rent_sample_size >= 10) as has_reliable_rent_sample
from feature_groups f
join strata s
  on s.prefecture is not distinct from f.prefecture
 and s.municipality is not distinct from f.municipality
 and s.ward is not distinct from f.ward
 and s.locality is not distinct from f.locality
 and s.layout_normalized is not distinct from f.layout_normalized
 and s.area_band is not distinct from f.area_band
