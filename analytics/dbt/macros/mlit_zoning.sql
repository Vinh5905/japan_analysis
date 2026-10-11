{% macro mlit_percent(expr) -%}
    case
        when nullif(trim(normalize({{ expr }}, nfkc)), '') ~ '^[0-9]+([.][0-9]+)?%?$'
        then replace(trim(normalize({{ expr }}, nfkc)), '%', '')::numeric
    end
{%- endmacro %}
{% macro mlit_location_fingerprint(alias) -%}
    md5(
        jsonb_build_array(
            {{ alias }}.latitude,
            {{ alias }}.longitude,
            {{ alias }}.provider,
            {{ alias }}.place_id,
            {{ alias }}.location_status,
            {{ alias }}.coordinate_level
        )::text
    )
{%- endmacro %}
{% macro mlit_business_signature(alias) -%}
    md5(
        jsonb_build_array(
            {{ alias }}.zoning_status,
            {{ alias }}.zoning_code,
            {{ alias }}.zoning_name,
            {{ alias }}.far_pct,
            {{ alias }}.bcr_pct
        )::text
    )
{%- endmacro %}
{% macro mlit_zoning_output(base, publication_run_id=none) %}
    with
        base as (select * from {{ ref(base) }}),
        publication as (
            select r.*
            from {{ source("zoning_operations", "zoning_runs") }} r
            {% if publication_run_id %}
                where
                    r.run_id = '{{ publication_run_id }}'
                    and r.publication_sequence is not null
            {% else %}
                join
                    {{ source("zoning_operations", "zoning_publication_pointer") }} p
                    using (run_id)
                where p.city_code = '27100'
            {% endif %}
        ),
        joined as (
            select
                b.*,
                p.run_id as zoning_publication_run_id,
                p.dataset_key as zoning_dataset_key,
                p.publication_sequence,
                p.published_at as zoning_published_at,
                m.zoning_area_key,
                m.zoning_status as published_status,
                m.zoning_code as candidate_zoning_code,
                m.zoning_name as candidate_zoning_name,
                m.far_pct as candidate_far_pct,
                m.bcr_pct as candidate_bcr_pct,
                m.boundary_distance_m,
                m.candidate_areas,
                d.source_as_of_date,
                d.source_modified_date,
                a.source_effective_date,
                i.location_fingerprint as published_location_fingerprint,
                current_input.location_fingerprint as current_location_fingerprint,
                v.building_zoning_version_key
            from base b
            left join publication p on true
            left join
                {{ ref("int_mlit__published_results") }} m
                on m.run_id = p.run_id
                and m.building_key = b.building_key
            left join
                {{ source("zoning_operations", "zoning_run_inputs") }} i
                on i.run_id = p.run_id
                and i.building_key = b.building_key
            left join
                {{ ref("int_suumo__zoning_inputs") }} current_input
                on current_input.building_key = b.building_key
            left join {{ ref("stg_mlit__datasets") }} d on d.dataset_key = p.dataset_key
            left join
                {{ ref("int_mlit__dataset_areas") }} a
                on a.dataset_key = p.dataset_key
                and a.zoning_area_key = m.zoning_area_key
            left join
                {{ ref("bridge_building_zoning") }} v
                on v.building_key = b.building_key
                and p.publication_sequence >= v.valid_from_sequence
                and (
                    v.valid_to_sequence is null
                    or p.publication_sequence < v.valid_to_sequence
                )
        ),
        classified as (
            select
                *,
                case
                    when zoning_publication_run_id is null
                    then 'no_publication'
                    when published_status is null
                    then 'no_snapshot_input'
                    {% if not publication_run_id %}
                        when
                            current_location_fingerprint
                            is distinct from published_location_fingerprint
                        then 'stale_location'
                    {% endif %}
                    else published_status
                end as zoning_status
            from joined
        )
    select
        base.*,
        c.zoning_status,
        case
            when c.zoning_status = 'matched' then c.candidate_zoning_code
        end as zoning_code,
        case
            when c.zoning_status = 'matched' then c.candidate_zoning_name
        end as zoning_name,
        case when c.zoning_status = 'matched' then c.candidate_far_pct end as far_pct,
        case when c.zoning_status = 'matched' then c.candidate_bcr_pct end as bcr_pct,
        c.building_zoning_version_key,
        c.zoning_area_key,
        c.zoning_publication_run_id,
        c.zoning_dataset_key,
        c.zoning_published_at,
        c.source_as_of_date as zoning_source_as_of_date,
        c.source_modified_date as zoning_source_modified_date,
        c.source_effective_date as zoning_source_effective_date,
        c.boundary_distance_m as zoning_boundary_distance_m
    from base
    join classified c using (task_id)
{% endmacro %}

{% macro mlit_immutable_results_hook() %}
DO $guard$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger
        WHERE tgrelid = '{{ this }}'::regclass
          AND tgname = 'immutable_matches'
    ) THEN
        EXECUTE 'CREATE TRIGGER immutable_matches'
            || ' BEFORE UPDATE OR DELETE ON {{ this }}'
            || ' FOR EACH ROW EXECUTE FUNCTION'
            || ' enrichment.reject_snapshot_mutation()';
    END IF;
END $guard$;
{% endmacro %}
