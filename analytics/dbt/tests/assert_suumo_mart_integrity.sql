with expected as (
    select task_id from {{ ref('int_suumo__mart_observations') }}
), coverage as (
    select coalesce(e.task_id, f.task_id) as task_id
    from expected e full join {{ ref('fct_rental_price_observation') }} f using (task_id)
    where e.task_id is null or f.task_id is null
), classification as (
    select h.task_id
    from {{ ref('int_suumo_rentals_history') }} h
    left join expected e using (task_id)
    left join {{ ref('rental_price_mart_rejects') }} r using (task_id)
    where (e.task_id is null) = (r.task_id is null)
), interval_errors as (
    select f.task_id
    from {{ ref('fct_rental_price_observation') }} f
    join {{ ref('int_suumo__mart_observations') }} o using (task_id)
    join {{ ref('dim_rental_listing') }} d using (listing_version_key)
    where d.source_id <> o.source_id or d.suumo_property_code <> o.suumo_property_code
       or (f.parsed_at_utc, f.task_id) < (d.effective_from_parsed_at_utc, d.effective_from_task_id)
       or (d.effective_to_task_id is not null and
           (f.parsed_at_utc, f.task_id) >= (d.effective_to_parsed_at_utc, d.effective_to_task_id))
       or f.exclusive_area_m2 is distinct from o.exclusive_area_m2
), scd_errors as (
    select min(effective_from_task_id) as task_id
    from {{ ref('dim_rental_listing') }}
    group by source_id, suumo_property_code
    having count(*) filter (where is_current_version) <> 1
        or count(distinct version_number) <> count(*)
        or min(version_number) <> 1 or max(version_number) <> count(*)
), ordered as (
    select *, lead(effective_from_parsed_at_utc) over w as expected_to_ts,
              lead(effective_from_task_id) over w as expected_to_task
    from {{ ref('dim_rental_listing') }}
    window w as (partition by source_id, suumo_property_code order by version_number)
), boundary_errors as (
    select effective_from_task_id as task_id from ordered
    where effective_to_parsed_at_utc is distinct from expected_to_ts
       or effective_to_task_id is distinct from expected_to_task
       or is_current_version is distinct from (expected_to_task is null)
), latest_errors as (
    select min(task_id) as task_id from {{ ref('rental_prices_latest_known') }}
    group by source_id, suumo_property_code having count(*) <> 1
)
select 'coverage' as issue, task_id from coverage
union all select 'classification', task_id from classification
union all select 'interval', task_id from interval_errors
union all select 'scd_versions', task_id from scd_errors
union all select 'scd_boundaries', task_id from boundary_errors
union all select 'latest', task_id from latest_errors
