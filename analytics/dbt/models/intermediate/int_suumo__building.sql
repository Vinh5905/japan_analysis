-- Physical unit and building structure, including floor consistency.
with parsed as (
    select task_id, n_age, n_floor, n_building_floors,
           case when {{ suumo_norm('exclusive_area_text') }} ~* '^[0-9]+(\.[0-9]+)? *(m2|m²|㎡)$'
                then nullif((regexp_match({{ suumo_norm('exclusive_area_text') }}, '^([0-9]+(\.[0-9]+)?)'))[1]::numeric, 0) end as exclusive_area_m2,
           case when n_age = '新築' then 0
                when n_age ~ '^築[0-9]+年(以上)?$' then (regexp_match(n_age, '^築([0-9]+)'))[1]::integer end as building_age_years,
           case when n_floor ~ '^[0-9]+(-[0-9]+)?階$'
                     and (regexp_match(n_floor, '^([0-9]+)'))[1]::integer >= 1
                     and coalesce((regexp_match(n_floor, '-([0-9]+)階$'))[1]::integer,
                                  (regexp_match(n_floor, '^([0-9]+)'))[1]::integer)
                         >= (regexp_match(n_floor, '^([0-9]+)'))[1]::integer
                then (regexp_match(n_floor, '^([0-9]+)'))[1]::integer end as floor_min,
           case when n_building_floors = '平屋' then 1
                when n_building_floors ~ '^([0-9]+(-[0-9]+)?階/)?(地下[0-9]+地上|地上)?[0-9]+階建$'
                then (regexp_match(n_building_floors, '([0-9]+)階建$'))[1]::integer end as building_total_floors_unchecked,
           {{ suumo_int_match('total_units', "'^([0-9]+)戸$'") }} as total_units_raw,
           {{ suumo_clean('building_type') }} as building_type_clean,
           {{ suumo_clean('structure') }} as structure_clean,
           {{ suumo_clean('direction') }} as direction_clean
    from {{ ref('stg_suumo_parser_records') }}
), checked as (
    select task_id, exclusive_area_m2, building_age_years,
           (building_age_years is not null and n_age like '%以上') as building_age_is_lower_bound,
           floor_min,
           case when floor_min is not null then coalesce((regexp_match(n_floor, '-([0-9]+)階$'))[1]::integer, floor_min) end as floor_max,
           case when building_total_floors_unchecked >= 1
                      and (regexp_match(n_building_floors, '^([0-9]+)(-([0-9]+))?階/'))[1]::integer is null
                then building_total_floors_unchecked
                when building_total_floors_unchecked >= 1
                     and (regexp_match(n_building_floors, '^([0-9]+)(-([0-9]+))?階/'))[1]::integer >= 1
                     and coalesce((regexp_match(n_building_floors, '^[0-9]+-([0-9]+)階/'))[1]::integer,
                                  (regexp_match(n_building_floors, '^([0-9]+)階/'))[1]::integer)
                         <= building_total_floors_unchecked
                then building_total_floors_unchecked end as building_total_floors,
           case when total_units_raw > 0 then total_units_raw end as total_units_count,
           building_type_clean, structure_clean, direction_clean
    from parsed
)
select task_id, exclusive_area_m2, building_age_years, building_age_is_lower_bound,
       floor_min, floor_max, case when floor_min = floor_max then floor_min end as floor_number,
       building_total_floors, total_units_count, building_type_clean, structure_clean, direction_clean,
       coalesce(floor_max > building_total_floors, false) as flag_floor_exceeds_building
from checked
