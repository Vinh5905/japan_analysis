-- All consumers use the building point; preserve one result per fact task.
with
    history as (
        select o.task_id
        from {{ ref("rental_price_observations") }} o
        join {{ ref("dim_building") }} b using (building_version_key)
        where
            o.latitude is distinct from b.latitude
            or o.longitude is distinct from b.longitude
            or o.building_full_address is distinct from b.building_full_address
    ),
    latest as (
        select o.task_id
        from {{ ref("rental_listing_latest") }} o
        join {{ ref("dim_building") }} b using (building_version_key)
        where
            o.latitude is distinct from b.latitude
            or o.longitude is distinct from b.longitude
    ),
    counts as (
        select -1::bigint as task_id
        where
            (select count(*) from {{ ref("fct_rental_price_observation") }})
            <> (select count(*) from {{ ref("rental_price_observations") }})
            or (select count(*) from {{ ref("rental_price_observations") }}) <> (
                select count(distinct task_id)
                from {{ ref("rental_price_observations") }}
            )
    )
select *
from history
union all
select *
from latest
union all
select *
from counts
