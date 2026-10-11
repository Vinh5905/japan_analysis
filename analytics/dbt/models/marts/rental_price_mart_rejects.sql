{{ config(materialized="view") }}
-- Never collapse observations without a business identity into one listing.
select
    task_id,
    source_id,
    suumo_property_code,
    parsed_at_utc,
    case
        when is_valid is not true
        then 'invalid_record'
        when source_id is null
        then 'missing_source_id'
        when nullif(btrim(suumo_property_code), '') is null
        then 'missing_listing_code'
        when parsed_at_utc is null
        then 'missing_parsed_at'
    end as reject_reason
from {{ ref("int_suumo_rentals_history") }}
where
    is_valid is not true
    or source_id is null
    or nullif(btrim(suumo_property_code), '') is null
    or parsed_at_utc is null
