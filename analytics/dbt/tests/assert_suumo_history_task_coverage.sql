-- Every valid raw task must appear once in the historical intermediate table.
with
    missing_from_history as (
        select task_id
        from {{ ref("stg_suumo_parser_records") }}
        except
        select task_id
        from {{ ref("int_suumo_rentals_history") }}
    ),
    unexpected_in_history as (
        select task_id
        from {{ ref("int_suumo_rentals_history") }}
        except
        select task_id
        from {{ ref("stg_suumo_parser_records") }}
    )
select task_id
from missing_from_history
union all
select task_id
from unexpected_in_history
