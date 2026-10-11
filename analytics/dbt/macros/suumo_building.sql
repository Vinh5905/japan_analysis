{% macro suumo_building_name(value) -%}
    nullif(
        lower(
            regexp_replace(
                normalize(coalesce(({{ value }})::text, ''), nfkc),
                '[[:space:]]',
                '',
                'g'
            )
        ),
        ''
    )
{%- endmacro %}

{% macro suumo_building_key(source, code, geography, name, address_query) -%}
    case
        when {{ name }} is not null and {{ address_query }} is not null
        then
            md5(
                jsonb_build_array(
                    'named_candidate_v1', {{ source }}, {{ geography }}, {{ name }}
                )::text
            )
        else
            md5(
                jsonb_build_array(
                    'unresolved_listing_v1', {{ source }}, {{ code }}
                )::text
            )
    end
{%- endmacro %}

{% macro suumo_building_timeline(relation) %}
    {% set fields = [
        "building_type",
        "structure",
        "building_total_floors",
        "total_units_count",
        "built_at",
        "built_at_precision",
        "geography_key",
    ] %}
    -- Date is source business time; parsed timestamp and task break ties. NULL means
    -- unknown, not deletion: carry known descriptors forward, never from the future.
    with
        dated as (
            select
                o.*,
                coalesce(
                    information_updated_at::timestamp at time zone 'Asia/Tokyo',
                    parsed_at_utc
                ) as building_effective_at_utc,
                case
                    when information_updated_at is null
                    then 'observation_time'
                    else 'source_update_date'
                end as building_event_time_basis
            from {{ relation }} o
        ),
        grouped as (
            select
                *,
                {% for field in fields %}
                    count(building_attributes ->> '{{ field }}') over w
                    as group_{{ field }}
                    {% if not loop.last %},{% endif %}
                {% endfor %}
            from dated
            window
                w as (
                    partition by building_key
                    order by building_effective_at_utc, parsed_at_utc, task_id
                    rows unbounded preceding
                )
        ),
        filled as (
            select
                *,
                jsonb_build_object(
                    {% for field in fields %}
                        '{{ field }}',
                        max(building_attributes ->> '{{ field }}') over (
                            partition by building_key, group_{{ field }}
                        )
                        {% if not loop.last %},{% endif %}
                    {% endfor %}
                ) as filled_attributes,
                information_updated_at is not null
                and (
                    {% for field in fields %}
                        min(building_attributes ->> '{{ field }}') over day
                        is distinct from max(
                            building_attributes ->> '{{ field }}'
                        ) over day
                        {% if not loop.last %} or {% endif %}
                    {% endfor %}
                ) as building_attributes_conflict
            from grouped
            window day as (partition by building_key, information_updated_at)
        ),
        previous as (
            select *, lag(filled_attributes) over w as previous_attributes
            from filled
            window
                w as (
                    partition by building_key
                    order by building_effective_at_utc, parsed_at_utc, task_id
                )
        ),
        boundaries as (
            select
                *,
                (filled_attributes is distinct from previous_attributes)::integer
                as starts_version
            from previous
        ),
        numbered as (
            select
                *,
                sum(starts_version) over (
                    partition by building_key
                    order by building_effective_at_utc, parsed_at_utc, task_id
                    rows unbounded preceding
                )::integer as version_number
            from boundaries
        ),
        starts as (
            select
                building_key,
                version_number,
                building_effective_at_utc as effective_from_utc,
                parsed_at_utc as effective_from_observed_at_utc,
                task_id as effective_from_task_id
            from numbered
            where starts_version = 1
        ),
        versions as (
            select
                *,
                md5(
                    jsonb_build_array(building_key, effective_from_task_id)::text
                ) as building_version_key,
                lead(effective_from_utc) over w as effective_to_utc,
                lead(effective_from_observed_at_utc) over w
                as effective_to_observed_at_utc,
                lead(effective_from_task_id) over w as effective_to_task_id
            from starts
            window w as (partition by building_key order by version_number)
        )
    select
        n.task_id,
        n.source_id,
        n.suumo_property_code,
        n.parsed_at_utc,
        n.building_key,
        n.building_identity_status,
        n.building_name_normalized,
        n.geography_key,
        n.information_updated_at,
        n.building_effective_at_utc,
        n.building_event_time_basis,
        n.building_attributes_conflict,
        n.filled_attributes as building_attributes,
        n.version_number,
        v.building_version_key,
        v.effective_from_utc,
        v.effective_from_observed_at_utc,
        v.effective_from_task_id,
        v.effective_to_utc,
        v.effective_to_observed_at_utc,
        v.effective_to_task_id,
        v.effective_to_task_id is null as is_current
    from numbered n
    join versions v using (building_key, version_number)
{% endmacro %}
