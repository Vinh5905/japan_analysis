with
    mapped as (
        select o.task_id
        from {{ ref("int_suumo__mart_observations") }} o
        left join {{ ref("int_suumo__building_timeline") }} t using (task_id)
        left join {{ ref("fct_rental_price_observation") }} f using (task_id)
        left join
            {{ ref("dim_building") }} b
            on f.building_version_key = b.building_version_key
        where
            t.task_id is null
            or b.building_version_key is null
            or t.building_version_key is distinct from f.building_version_key
            or b.building_key is distinct from t.building_key
            or (t.building_effective_at_utc, t.parsed_at_utc, t.task_id) < (
                b.effective_from_utc,
                b.effective_from_observed_at_utc,
                b.effective_from_task_id
            )
            or (
                b.effective_to_task_id is not null
                and (t.building_effective_at_utc, t.parsed_at_utc, t.task_id) >= (
                    b.effective_to_utc,
                    b.effective_to_observed_at_utc,
                    b.effective_to_task_id
                )
            )
            or f.building_age_years is distinct from o.building_age_years
            or f.building_age_is_lower_bound
            is distinct from o.building_age_is_lower_bound
            or o.listing_attributes ?| array[
                'building_type',
                'structure',
                'building_total_floors',
                'total_units_count',
                'built_at',
                'built_at_precision',
                'building_age_years',
                'building_age_is_lower_bound'
            ]
    ),
    scd as (
        select min(effective_from_task_id) as task_id
        from {{ ref("dim_building") }}
        group by building_key
        having
            count(*) filter (where is_current) <> 1
            or count(distinct version_number) <> count(*)
            or min(version_number) <> 1
            or max(version_number) <> count(*)
    ),
    ordered as (
        select
            *,
            lead(effective_from_utc) over w as next_date,
            lead(effective_from_observed_at_utc) over w as next_observed,
            lead(effective_from_task_id) over w as next_task
        from {{ ref("dim_building") }}
        window w as (partition by building_key order by version_number)
    )
select 'mapping' as issue, task_id
from mapped
union all
select 'scd', task_id
from scd
union all
select 'boundaries', effective_from_task_id
from ordered
where
    effective_to_utc is distinct from next_date
    or effective_to_observed_at_utc is distinct from next_observed
    or effective_to_task_id is distinct from next_task
    or is_current is distinct from (next_task is null)
