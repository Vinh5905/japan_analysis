{{ config(materialized="table", indexes=[{"columns": ["task_id"], "unique": true}]) }}
{{ suumo_building_timeline(ref("int_suumo__building_events")) }}
