-- Same name/address groups candidates; preserve wings and isolate missing names.
with
    fixture as (
        select
            id,
            source_id::bigint as source_id,
            code,
            geography,
            name,
            address,
            expected_group
        from
            (
                values
                    (1, 1, 'A', 'G', 'Ｗｅｓｔ　Gate', '大阪府大阪市淀川区十三本町2丁目', 1),
                    (2, 1, 'B', 'G', 'west gate', '大阪府大阪市淀川区十三本町2丁目', 1),
                    (3, 1, 'C', 'H', 'West Gate', '大阪府大阪市淀川区十三本町1丁目', 3),
                    (4, 1, 'D', 'G', 'West Gate弐番館', '大阪府大阪市淀川区十三本町2丁目', 4),
                    (5, 1, 'E', 'G', null, '大阪府大阪市淀川区十三本町2丁目', 5),
                    (6, 1, 'F', 'G', null, '大阪府大阪市淀川区十三本町2丁目', 6),
                    (7, 1, 'A', 'G', 'West Gate', null, 7),
                    (8, 2, 'A', 'G', 'West Gate', '大阪府大阪市淀川区十三本町2丁目', 8)
            ) v(id, source_id, code, geography, name, address, expected_group)
    ),
    normalized as (
        select *, {{ suumo_building_name("name") }} as normalized_name from fixture
    ),
    keys as (
        select
            *,
            {{
                suumo_building_key(
                    "source_id", "code", "geography", "normalized_name", "address"
                )
            }} as building_key
        from normalized
    )
select a.id
from keys a
join keys b on a.id < b.id
where
    (a.expected_group = b.expected_group)
    is distinct from (a.building_key = b.building_key)
