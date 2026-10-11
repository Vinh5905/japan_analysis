{{ config(materialized="view", tags=["mlit_zoning_output"]) }}
{{ mlit_zoning_output("rental_price_observations") }}
