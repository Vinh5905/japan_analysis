{{ config(indexes=[{'columns': ['date_key'], 'unique': true}]) }}
with bounds as (
    select min((parsed_at_utc at time zone 'Asia/Tokyo')::date) as first_date,
           max((parsed_at_utc at time zone 'Asia/Tokyo')::date) as last_date
    from {{ ref('int_suumo__mart_observations') }}
), dates as (
    select first_date + n as calendar_date
    from bounds cross join lateral generate_series(0, last_date - first_date) n
)
select to_char(calendar_date, 'YYYYMMDD')::integer as date_key, calendar_date,
       extract(day from calendar_date)::integer as day_of_month,
       extract(isodow from calendar_date)::integer as day_of_week,
       extract(week from calendar_date)::integer as iso_week,
       extract(isoyear from calendar_date)::integer as iso_week_year,
       extract(month from calendar_date)::integer as month_number,
       extract(quarter from calendar_date)::integer as quarter_number,
       extract(year from calendar_date)::integer as calendar_year,
       (extract(isodow from calendar_date) in (6, 7)) as is_weekend
from dates
