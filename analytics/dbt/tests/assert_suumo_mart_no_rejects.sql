{{ config(severity="warn") }}
-- Explicit observability without dropping otherwise usable listings.
select *
from {{ ref("rental_price_mart_rejects") }}
