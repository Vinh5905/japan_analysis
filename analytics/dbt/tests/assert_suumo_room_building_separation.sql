-- Changing a building descriptor is independent from room/listing SCD2.
with
    fixture as (
        select
            task_id,
            1::bigint as source_id,
            'A'::text as suumo_property_code,
            ts::timestamptz as parsed_at_utc,
            jsonb_build_object('room_number', room) as listing_attributes,
            jsonb_build_object('building_total_floors', floors) as building_attributes,
            expected_version
        from
            (
                values
                    (1::bigint, '2026-01-01 00:00Z', '203', 10, 1),
                    (2, '2026-01-02 00:00Z', '203', 11, 1),
                    (3, '2026-01-03 00:00Z', '204', 11, 2)
            ) v(task_id, ts, room, floors, expected_version)
    ),
    actual as ({{ suumo_listing_timeline("fixture") }})
select task_id
from fixture f
join actual a using (task_id)
where a.version_number <> f.expected_version
