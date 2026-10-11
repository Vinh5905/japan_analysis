-- Group 1: asking-price distribution at explicit, non-overlapping drill levels.
-- BI must filter market_level before summing listing_count.
with
    grouped as (
        select
            case
                when grouping(building_type) = 0
                then 'locality_layout_area_building'
                when grouping(area_band) = 0
                then 'locality_layout_area'
                when grouping(locality) = 0
                then 'locality'
                when grouping(ward) = 0
                then 'ward'
                else 'overall'
            end as market_level,
            prefecture,
            municipality,
            ward,
            locality,
            layout_normalized,
            area_band,
            min(area_band_sort) as area_band_sort,
            building_type,
            count(*)::bigint as listing_count,
            count(rent_jpy)::bigint as rent_sample_size,
            count(base_monthly_cost_jpy)::bigint as base_monthly_cost_sample_size,
            count(rent_per_m2_jpy)::bigint as rent_per_m2_sample_size,
            percentile_cont(0.25) within group (order by rent_jpy) filter (
                where rent_jpy is not null
            ) as rent_p25_jpy,
            percentile_cont(0.50) within group (order by rent_jpy) filter (
                where rent_jpy is not null
            ) as rent_median_jpy,
            percentile_cont(0.75) within group (order by rent_jpy) filter (
                where rent_jpy is not null
            ) as rent_p75_jpy,
            avg(rent_jpy)::numeric(18, 2) as rent_average_jpy,
            percentile_cont(0.50) within group (order by base_monthly_cost_jpy) filter (
                where base_monthly_cost_jpy is not null
            ) as base_monthly_cost_median_jpy,
            percentile_cont(0.50) within group (order by rent_per_m2_jpy) filter (
                where rent_per_m2_jpy is not null
            ) as rent_per_m2_median_jpy
        from {{ ref("rental_listing_latest") }}
        group by
            grouping sets (
                (),
                (prefecture, municipality, ward),
                (prefecture, municipality, ward, locality),
                (
                    prefecture,
                    municipality,
                    ward,
                    locality,
                    layout_normalized,
                    area_band
                ),
                (
                    prefecture,
                    municipality,
                    ward,
                    locality,
                    layout_normalized,
                    area_band,
                    building_type
                )
            )
    )
select
    md5(
        jsonb_build_array(
            market_level,
            prefecture,
            municipality,
            ward,
            locality,
            layout_normalized,
            area_band,
            building_type
        )::text
    ) as market_segment_key,
    *,
    rent_sample_size >= 5 as has_reliable_rent_sample,
    rent_sample_size::numeric / nullif(listing_count, 0) as rent_coverage_ratio,
    base_monthly_cost_sample_size::numeric
    / nullif(listing_count, 0) as base_monthly_cost_coverage_ratio,
    rent_per_m2_sample_size::numeric
    / nullif(listing_count, 0) as rent_per_m2_coverage_ratio
from grouped
