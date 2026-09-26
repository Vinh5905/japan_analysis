{{ config(materialized='table', indexes=[{'columns': ['task_id'], 'unique': true}]) }}
{{ suumo_listing_timeline(ref('int_suumo__mart_observations')) }}
