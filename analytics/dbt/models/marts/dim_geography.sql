{{ config(indexes=[{'columns': ['geography_key'], 'unique': true}]) }}
select distinct geography_key,
       geography_attributes ->> 'prefecture' as prefecture,
       geography_attributes ->> 'district' as district,
       geography_attributes ->> 'municipality' as municipality,
       geography_attributes ->> 'ward' as ward,
       geography_attributes ->> 'locality' as locality,
       geography_attributes ->> 'chome' as chome
from {{ ref('int_suumo__mart_observations') }}
