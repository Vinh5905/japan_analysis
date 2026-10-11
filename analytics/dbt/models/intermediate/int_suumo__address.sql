-- Keep the multi-step Japanese address parser isolated for inspection.
with
    source as (
        select task_id, address, n_address from {{ ref("stg_suumo_parser_records") }}
    ),
    address_parts as (
        select
            task_id,
            (
                regexp_match(
                    n_address,
                    '^(北海道|東京都|京都府|大阪府|青森県|岩手県|宮城県|秋田県|山形県|福島県|茨城県|栃木県|群馬県|埼玉県|千葉県|神奈川県|新潟県|富山県|石川県|福井県|山梨県|長野県|岐阜県|静岡県|愛知県|三重県|滋賀県|兵庫県|奈良県|和歌山県|鳥取県|島根県|岡山県|広島県|山口県|徳島県|香川県|愛媛県|高知県|福岡県|佐賀県|長崎県|熊本県|大分県|宮崎県|鹿児島県|沖縄県)'
                )
            )[1] as prefecture,
            n_address
        from source
    ),
    address_rest as (
        select
            task_id,
            prefecture,
            substring(n_address from char_length(coalesce(prefecture, '')) + 1) as rest
        from address_parts
    ),
    address_district as (
        select
            task_id,
            prefecture,
            (regexp_match(rest, '^([^市区町村]+郡)'))[1] as district,
            rest
        from address_rest
    ),
    address_city as (
        select
            task_id,
            prefecture,
            district,
            case
                when
                    substring(rest from char_length(coalesce(district, '')) + 1)
                    like '大阪市%'
                then '大阪市'
                when
                    substring(rest from char_length(coalesce(district, '')) + 1)
                    like '堺市%'
                then '堺市'
                else
                    (
                        regexp_match(
                            substring(
                                rest from char_length(coalesce(district, '')) + 1
                            ),
                            '^(.+?(市|町|村))'
                        )
                    )[1]
            end as municipality,
            substring(rest from char_length(coalesce(district, '')) + 1) as rest
        from address_district
    ),
    address_ward as (
        select
            task_id,
            prefecture,
            district,
            municipality,
            case
                when municipality in ('大阪市', '堺市')
                then
                    (
                        regexp_match(
                            substring(rest from char_length(municipality) + 1),
                            '^([^市区町村郡]+区)'
                        )
                    )[1]
            end as ward,
            substring(rest from char_length(coalesce(municipality, '')) + 1) as rest
        from address_city
    ),
    address_final as (
        select
            task_id,
            prefecture,
            district,
            municipality,
            ward,
            substring(rest from char_length(coalesce(ward, '')) + 1) as tail
        from address_ward
    )
select
    s.task_id,
    s.address as address_raw,
    a.prefecture,
    a.district,
    a.municipality,
    a.ward,
    case
        when a.tail ~ '^.+?[0-9]{1,3}丁目'
        then (regexp_match(a.tail, '^(.+?)[0-9]{1,3}丁目'))[1]
        when a.tail ~ '^.+?[一二三四五六七八九十]+丁目'
        then (regexp_match(a.tail, '^(.+?)[一二三四五六七八九十]+丁目'))[1]
        when a.tail !~ '[-－ー]' and a.tail ~ '[一-龯ぁ-んァ-ン][0-9]{1,3}$'
        then (regexp_match(a.tail, '^(.*[一-龯ぁ-んァ-ン])[0-9]{1,3}$'))[1]
        else a.tail
    end as locality,
    case
        when a.tail ~ '^.+?[0-9]{1,3}丁目'
        then (regexp_match(a.tail, '^.+?([0-9]{1,3})丁目'))[1]::integer
        when a.tail ~ '^.+?[一二三四五六七八九十]+丁目'
        then
            {{
                suumo_kanji_int(
                    "(regexp_match(a.tail, '^.+?([一二三四五六七八九十]+)丁目'))[1]"
                )
            }}
        when a.tail !~ '[-－ー]' and a.tail ~ '[一-龯ぁ-んァ-ン][0-9]{1,3}$'
        then (regexp_match(a.tail, '([0-9]{1,3})$'))[1]::integer
    end as chome
from source s
left join address_final a using (task_id)
