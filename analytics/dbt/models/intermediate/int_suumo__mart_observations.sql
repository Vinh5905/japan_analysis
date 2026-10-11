{{ config(materialized="table", indexes=[{"columns": ["task_id"], "unique": true}]) }}
-- Mart boundary: explicit identity eligibility, conservative descriptors and fees.
with
    station_quality as (
        select
            task_id,
            case
                when bool_and(parse_status = 'parsed')
                then 'full'
                when bool_or(parse_status = 'parsed')
                then 'partial'
                else 'failed'
            end as station_access_parse_status
        from {{ ref("int_suumo__station_access") }}
        group by task_id
    ),
    prepared as (
        select
            h.task_id,
            h.source_id,
            btrim(h.suumo_property_code) as suumo_property_code,
            h.record_origin,
            h.parsed_at_utc,
            h.information_updated_at,
            h.building_name,
            h.building_name_normalized,
            h.name_parse_status,
            h.name_source,
            h.building_age_years,
            h.building_age_is_lower_bound,
            to_jsonb(b) as building_attributes,
            to_jsonb(d) as listing_attributes,
            to_jsonb(g) as geography_attributes,
            to_jsonb(q) as quality_attributes,
            h.rent_jpy,
            p.management_fee_jpy,
            p.deposit_jpy,
            p.key_money_jpy,
            p.guarantee_deposit_jpy,
            p.depreciation_jpy,
            coalesce(
                p.brokerage_fee_jpy, round(h.brokerage_fee_months * h.rent_jpy)::bigint
            ) as brokerage_fee_amount_jpy,
            h.other_initial_costs_total_jpy,
            h.insurance_jpy,
            h.parking_fee_jpy,
            h.exclusive_area_m2
        from {{ ref("int_suumo_rentals_history") }} h
        left join station_quality s using (task_id)
        cross join
            lateral(
                select
                    {{ suumo_mart_jpy("h.management_fee_text") }} as management_fee_jpy,
                    {{ suumo_mart_jpy("h.deposit_text") }} as deposit_jpy,
                    {{ suumo_mart_jpy("h.key_money_text") }} as key_money_jpy,
                    {{ suumo_mart_jpy("h.guarantee_deposit_text") }}
                    as guarantee_deposit_jpy,
                    {{ suumo_mart_jpy("h.depreciation_text") }} as depreciation_jpy,
                    {{ suumo_mart_jpy("h.brokerage_fee") }} as brokerage_fee_jpy
            ) p
        cross join
            lateral(
                select
                    h.direction_clean as direction,
                    h.room_number as room_number,
                    h.floor_min as floor_min,
                    h.floor_max as floor_max,
                    h.floor_number as floor_number,
                    h.layout_room_count as layout_room_count,
                    h.layout_normalized as layout_normalized,
                    h.layout_has_service_room as layout_has_service_room,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.layout_space_count
                    end as layout_space_count,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.western_room_count
                    end as western_room_count,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.japanese_room_count
                    end as japanese_room_count,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.service_room_count
                    end as service_room_count,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.largest_private_room_jo
                    end as largest_private_room_jo,
                    case
                        when h.layout_detail_parse_status = 'full' then h.kitchen_type
                    end as kitchen_type,
                    case
                        when h.layout_detail_parse_status = 'full'
                        then h.kitchen_size_jo
                    end as kitchen_size_jo,
                    case
                        when h.layout_detail_parse_status = 'full' then h.loft_present
                    end as loft_present,
                    case
                        when h.layout_detail_parse_status = 'full' then h.loft_size_jo
                    end as loft_size_jo,
                    h.transaction_type_clean as transaction_type,
                    h.contract_type as contract_type,
                    h.contract_years as contract_years,
                    h.contract_months as contract_months,
                    h.move_in_status as move_in_status,
                    h.move_in_month as move_in_month,
                    h.move_in_period as move_in_period,
                    h.insurance_required as insurance_required,
                    h.insurance_period_years as insurance_period_years,
                    h.brokerage_fee_months as brokerage_fee_months,
                    h.parking_location as parking_location,
                    h.parking_distance_m as parking_distance_m,
                    h.parking_detail as parking_detail,
                    h.parking_max_spaces as parking_max_spaces,
                    case
                        when h.parking_listed then 'listed' else 'unknown'
                    end as parking_listing_status,
                    case
                        when p.brokerage_fee_jpy is not null
                        then 'reported_jpy'
                        when
                            h.brokerage_fee_months is not null
                            and h.rent_jpy is not null
                        then 'estimated_from_months'
                        else 'unknown'
                    end as brokerage_fee_amount_basis,
                    {{ suumo_area_band("h.exclusive_area_m2") }} as area_band,
                    case
                        when h.exclusive_area_m2 is null or h.exclusive_area_m2 <= 0
                        then 0
                        when h.exclusive_area_m2 < 20
                        then 1
                        when h.exclusive_area_m2 < 30
                        then 2
                        when h.exclusive_area_m2 < 40
                        then 3
                        when h.exclusive_area_m2 < 50
                        then 4
                        when h.exclusive_area_m2 < 70
                        then 5
                        when h.exclusive_area_m2 < 100
                        then 6
                        else 7
                    end as area_band_sort
            ) d
        cross join
            lateral(
                select
                    h.building_type_clean as building_type,
                    h.structure_clean as structure,
                    h.building_total_floors,
                    h.total_units_count,
                    h.built_at,
                    h.built_at_precision
            ) b
        cross join
            lateral(
                select
                    h.prefecture,
                    h.district,
                    h.municipality,
                    h.ward,
                    h.locality,
                    h.chome
            ) g
        cross join
            lateral(
                select
                    h.flag_missing_core,
                    h.flag_floor_exceeds_building,
                    h.flag_layout_detail_parse_failure,
                    coalesce(
                        h.layout_detail_parse_status, 'missing'
                    ) as layout_detail_parse_status,
                    coalesce(
                        s.station_access_parse_status, 'missing'
                    ) as station_access_parse_status
            ) q
        where
            h.is_valid is true
            and h.source_id is not null
            and nullif(btrim(h.suumo_property_code), '') is not null
            and h.parsed_at_utc is not null
    )
select
    *,
    md5(geography_attributes::text) as geography_key,
    md5(quality_attributes::text) as observation_quality_key
from prepared
