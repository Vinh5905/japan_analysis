{{ config(tags=["mlit_zoning_output"]) }}
{% for base in [
    "rental_price_observations",
    "rental_prices_latest_known",
    "rental_listing_latest",
] %}
    select '{{ base }}' as model_name
    where
        (select count(*) from {{ ref(base) }})
        <> (select count(*) from {{ ref(base ~ "_with_zoning") }})
        or (select count(*) from {{ ref(base ~ "_with_zoning") }})
        <> (select count(distinct task_id) from {{ ref(base ~ "_with_zoning") }})
    {% if not loop.last %}
        union all
    {% endif %}
{% endfor %}
