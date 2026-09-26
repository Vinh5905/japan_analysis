{{ config(materialized='view') }}
-- Latest selection precedes geography/price/quality filtering in BI.
select * from {{ ref('rental_price_observations') }} where is_latest_known
