with expected as (
    select distinct geography_key from {{ ref('int_suumo__mart_observations') }}
), actual as (
    select geography_key from {{ ref('dim_geography') }}
)
select coalesce(e.geography_key, a.geography_key) as geography_key
from expected e full outer join actual a using (geography_key)
where e.geography_key is null or a.geography_key is null
