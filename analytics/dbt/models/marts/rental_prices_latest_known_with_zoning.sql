{{ config(materialized="view", tags=["mlit_zoning_output"]) }}
{{ mlit_zoning_output("rental_prices_latest_known") }}
