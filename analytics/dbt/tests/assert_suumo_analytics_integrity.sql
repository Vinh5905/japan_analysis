with
    latest_coverage as (
        select coalesce(l.task_id, a.task_id) as task_id
        from {{ ref("rental_prices_latest_known") }} l
        full join {{ ref("rental_listing_latest") }} a using (task_id)
        where l.task_id is null or a.task_id is null
    ),
    benchmark_coverage as (
        select coalesce(l.task_id, b.task_id) as task_id
        from {{ ref("rental_listing_latest") }} l
        full join {{ ref("rental_listing_comparable_benchmark") }} b using (task_id)
        where l.task_id is null or b.task_id is null
    ),
    benchmark_rules as (
        select task_id
        from {{ ref("rental_listing_comparable_benchmark") }}
        where
            (benchmark_tier = 'insufficient_sample' and peer_sample_size is not null)
            or (benchmark_tier <> 'insufficient_sample' and peer_sample_size < 5)
            or (peer_median_rent_jpy is null and rent_position <> 'not_scored')
    ),
    summary_rules as (
        select null::bigint as task_id
        from {{ ref("rental_market_price_summary") }}
        where
            listing_count <= 0
            or rent_sample_size > listing_count
            or base_monthly_cost_sample_size > listing_count
            or rent_per_m2_sample_size > listing_count
    ),
    feature_rules as (
        select null::bigint as task_id
        from {{ ref("rental_feature_price_summary") }}
        where
            listing_count <= 0
            or rent_sample_size > listing_count
            or rent_per_m2_sample_size > listing_count
            or has_reliable_rent_sample is distinct from (
                is_known_feature
                and rent_sample_size >= 5
                and stratum_rent_sample_size >= 10
            )
    )
select 'latest_coverage' as issue, task_id
from latest_coverage
union all
select 'benchmark_coverage', task_id
from benchmark_coverage
union all
select 'benchmark_rules', task_id
from benchmark_rules
union all
select 'summary_rules', task_id
from summary_rules
union all
select 'feature_rules', task_id
from feature_rules
