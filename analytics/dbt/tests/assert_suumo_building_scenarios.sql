-- Business-time late arrival, A->B->A, missing attributes, same-day conflict,
-- missing dates, timestamp/task tie breaking and a separately isolated identity.
with
    fixture as (
        select
            task_id,
            1::bigint as source_id,
            'listing'::text as suumo_property_code,
            observed::timestamptz as parsed_at_utc,
            updated::date as information_updated_at,
            identity as building_key,
            'named_candidate'::text as building_identity_status,
            'テスト'::text as building_name_normalized,
            'G'::text as geography_key,
            attrs::jsonb
            || jsonb_build_object('geography_key', 'G') as building_attributes,
            expected_version,
            expected_start,
            expected_end,
            expected_floors,
            conflict
        from
            (
                values
                    (
                        10::bigint,
                        'A',
                        '2026-01-06 00:00Z',
                        '2026-01-01',
                        '{"building_total_floors":10}',
                        1,
                        10::bigint,
                        30::bigint,
                        '10',
                        false
                    ),
                    (
                        20,
                        'A',
                        '2026-01-02 00:00Z',
                        '2026-01-02',
                        '{}',
                        1,
                        10,
                        30,
                        '10',
                        false
                    ),
                    (
                        30,
                        'A',
                        '2026-01-03 00:00Z',
                        '2026-01-03',
                        '{"building_total_floors":12}',
                        2,
                        30,
                        40,
                        '12',
                        false
                    ),
                    (
                        40,
                        'A',
                        '2026-01-04 00:00Z',
                        '2026-01-04',
                        '{"building_total_floors":10}',
                        3,
                        40,
                        60,
                        '10',
                        false
                    ),
                    (
                        50,
                        'A',
                        '2026-01-05 01:00Z',
                        '2026-01-05',
                        '{"building_total_floors":10}',
                        3,
                        40,
                        60,
                        '10',
                        true
                    ),
                    (
                        60,
                        'A',
                        '2026-01-05 02:00Z',
                        '2026-01-05',
                        '{"building_total_floors":12}',
                        4,
                        60,
                        71,
                        '12',
                        true
                    ),
                    (70, 'A', '2026-01-07 00:00Z', null, '{}', 4, 60, 71, '12', false),
                    (
                        71,
                        'A',
                        '2026-01-07 00:00Z',
                        null,
                        '{"building_total_floors":15}',
                        5,
                        71,
                        null,
                        '15',
                        false
                    ),
                    (
                        101,
                        'B',
                        '2026-01-01 00:00Z',
                        '2026-01-01',
                        '{}',
                        1,
                        101,
                        102,
                        null,
                        false
                    ),
                    (
                        102,
                        'B',
                        '2026-01-02 00:00Z',
                        '2026-01-02',
                        '{"structure":"木造"}',
                        2,
                        102,
                        null,
                        null,
                        false
                    ),
                    (
                        103,
                        'B',
                        '2026-01-03 00:00Z',
                        '2026-01-03',
                        '{}',
                        2,
                        102,
                        null,
                        null,
                        false
                    )
            ) v(
                task_id,
                identity,
                observed,
                updated,
                attrs,
                expected_version,
                expected_start,
                expected_end,
                expected_floors,
                conflict
            )
    ),
    actual as ({{ suumo_building_timeline("fixture") }})
select f.task_id
from fixture f
full join actual a using (task_id)
where
    f.task_id is null
    or a.task_id is null
    or a.version_number is distinct from f.expected_version
    or a.effective_from_task_id is distinct from f.expected_start
    or a.effective_to_task_id is distinct from f.expected_end
    or a.building_attributes
    ->> 'building_total_floors'
    is distinct from f.expected_floors
    or a.building_attributes_conflict is distinct from f.conflict
    or a.is_current is distinct from (f.expected_end is null)
    or a.building_version_key
    is distinct from md5(jsonb_build_array(f.building_key, f.expected_start)::text)
    or (f.task_id = 101 and a.building_attributes ->> 'structure' is not null)
    or (f.task_id = 103 and a.building_attributes ->> 'structure' <> '木造')
