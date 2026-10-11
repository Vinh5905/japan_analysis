{% macro suumo_geocode_part(value) -%}
    regexp_replace(
        coalesce(normalize(({{ value }})::text, nfkc), ''), '[[:space:]]', '', 'g'
    )
{%- endmacro %}

{% macro suumo_geocode_address_query(prefix) -%}
    {%- set fields = [
        "prefecture",
        "district",
        "municipality",
        "ward",
        "locality",
        "chome",
    ] -%}
    {%- set cleaned = {} -%}
    {%- for field in fields -%}
        {%- set text = suumo_geocode_part(prefix ~ "." ~ field) -%}
        {%- do cleaned.update(
            {
                field: "case when "
                ~ text
                ~ " in ('', 'nan', 'NaN', '<NA>', 'None', '-', '―') then '' else "
                ~ text
                ~ " end"
            }
        ) -%}
    {%- endfor -%}
    case
        when
            {{ cleaned.prefecture }} = ''
            or {{ cleaned.municipality }} = ''
            or {{ cleaned.locality }} = ''
        then null
        when {{ cleaned.chome }} ~ '^[0-9]+(\.0+)?$'
        then
            case
                when ({{ cleaned.chome }})::numeric between 1 and 9999
                then
                    {{ cleaned.prefecture }}
                    || {{ cleaned.district }}
                    || {{ cleaned.municipality }}
                    || {{ cleaned.ward }}
                    || {{ cleaned.locality }}
                    || ({{ cleaned.chome }})::numeric::integer::text
                    || '丁目'
            end
    end
{%- endmacro %}
