{% macro suumo_norm(value) -%}
    nullif(btrim(normalize(({{ value }})::text, nfkc)), '')
{%- endmacro %}

{% macro suumo_clean(value) -%}
    nullif(
        nullif(
            nullif(
                nullif(nullif(nullif({{ suumo_norm(value) }}, '-'), '―'), 'なし'), '無し'
            ),
            '未定'
        ),
        '－'
    )
{%- endmacro %}

{% macro suumo_jpy(value, zero=false) -%}
    case
        {% if zero %}
            when {{ suumo_norm(value) }} in ('-', '―', 'なし', '無し', '未定', '不要')
            then 0::bigint
        {% endif %}
        when {{ suumo_norm(value) }} ~ '^[0-9][0-9,]*(\.[0-9]+)? *(万円|円)$'
        then
            round(
                replace(
                    substring(
                        {{ suumo_norm(value) }} from '^([0-9][0-9,]*(\.[0-9]+)?)'
                    ),
                    ',',
                    ''
                )::numeric
                * case when {{ suumo_norm(value) }} like '%万円' then 10000 else 1 end
            )::bigint
        else null::bigint
    end
{%- endmacro %}

{% macro suumo_int_match(value, pattern, group=1) -%}
    case
        when {{ suumo_norm(value) }} ~ {{ pattern }}
        then
            (regexp_match({{ suumo_norm(value) }}, {{ pattern }}))[{{ group }}]::integer
        else null::integer
    end
{%- endmacro %}

{% macro suumo_kanji_int(value) -%}
    case
        when {{ value }} = '十'
        then 10
        when {{ value }} ~ '^[一二三四五六七八九]$'
        then translate({{ value }}, '一二三四五六七八九', '123456789')::integer
        when {{ value }} ~ '^[一二三四五六七八九]?十[一二三四五六七八九]?$'
        then
            coalesce(
                nullif(
                    split_part(
                        translate({{ value }}, '一二三四五六七八九', '123456789'), '十', 1
                    ),
                    ''
                ),
                '1'
            )::integer
            * 10
            + coalesce(
                nullif(
                    split_part(
                        translate({{ value }}, '一二三四五六七八九', '123456789'), '十', 2
                    ),
                    ''
                ),
                '0'
            )::integer
    end
{%- endmacro %}
