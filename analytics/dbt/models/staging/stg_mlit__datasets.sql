{{ config(materialized="mlit_stable_view", tags=["mlit_zoning_core"]) }}
select *
from {{ source("warehouse_raw", "mlit_datasets") }}
