{{ config(indexes=[{'columns': ['task_id', 'access_order'], 'unique': true},
                   {'columns': ['station_label_key']}]) }}
select s.task_id, s.access_order,
       d.station_label_key, s.parse_status, s.access_mode, s.total_travel_minutes
from {{ ref('int_suumo__station_access') }} s
join {{ ref('fct_rental_price_observation') }} f using (task_id)
join {{ ref('dim_rental_listing') }} l using (listing_version_key)
join {{ ref('dim_station_label') }} d
  on d.station_label_key = case when s.parse_status = 'parsed'
     then md5(jsonb_build_array(l.source_id, s.station_line, s.station_name)::text)
     else '00000000000000000000000000000000' end
