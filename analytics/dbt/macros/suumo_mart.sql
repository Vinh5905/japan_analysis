{% macro suumo_mart_jpy(value) -%}
    -- Unknown/undecided is not free. Leave existing intermediate semantics intact.
    case
        when {{ suumo_norm(value) }} in ('-', '―', '未定')
        then null::bigint
        else {{ suumo_jpy(value, true) }}
    end
{%- endmacro %}

{% macro suumo_listing_timeline(relation) %}
    -- Reconstruct consecutive descriptor runs from all available observations.
    -- Comparing JSONB preserves NULL distinctions without delimiter collisions.
    with
        previous as (
            select
                o.*,
                lag(listing_attributes) over (
                    partition by source_id, suumo_property_code
                    order by parsed_at_utc, task_id
                ) as previous_attributes
            from {{ relation }} o
        ),
        boundaries as (
            select
                *,
                case
                    when listing_attributes is distinct from previous_attributes
                    then 1
                    else 0
                end as starts_version
            from previous
        ),
        numbered as (
            select
                *,
                sum(starts_version) over (
                    partition by source_id, suumo_property_code
                    order by parsed_at_utc, task_id
                    rows unbounded preceding
                )::integer as version_number
            from boundaries
        ),
        starts as (
            select
                source_id,
                suumo_property_code,
                version_number,
                parsed_at_utc as effective_from_parsed_at_utc,
                task_id as effective_from_task_id
            from numbered
            where starts_version = 1
        ),
        versions as (
            select
                *,
                md5(
                    jsonb_build_array(
                        source_id, suumo_property_code, effective_from_task_id
                    )::text
                ) as listing_version_key,
                lead(effective_from_parsed_at_utc) over w as effective_to_parsed_at_utc,
                lead(effective_from_task_id) over w as effective_to_task_id
            from starts
            window
                w as (
                    partition by source_id, suumo_property_code order by version_number
                )
        )
    select
        n.task_id,
        n.source_id,
        n.suumo_property_code,
        n.parsed_at_utc,
        n.listing_attributes,
        n.version_number,
        v.listing_version_key,
        v.effective_from_parsed_at_utc,
        v.effective_from_task_id,
        v.effective_to_parsed_at_utc,
        v.effective_to_task_id,
        (v.effective_to_task_id is null) as is_current_version
    from numbered n
    join versions v using (source_id, suumo_property_code, version_number)
{% endmacro %}

{% macro suumo_area_band(value) -%}
    case
        when {{ value }} is null or {{ value }} <= 0
        then 'unknown'
        when {{ value }} < 20
        then '<20'
        when {{ value }} < 30
        then '20-<30'
        when {{ value }} < 40
        then '30-<40'
        when {{ value }} < 50
        then '40-<50'
        when {{ value }} < 70
        then '50-<70'
        when {{ value }} < 100
        then '70-<100'
        else '>=100'
    end
{%- endmacro %}
