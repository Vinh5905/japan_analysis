-- Executable business scenarios: price-only/unchanged observations, A->B->A,
-- late arrival (input deliberately unordered), equal timestamps, NULL values,
-- source-scoped identity, and an independent new listing.
with fixture as (
    select task_id, source_id, code as suumo_property_code,
           ts::timestamptz as parsed_at_utc, attrs::jsonb as listing_attributes,
           rent_jpy, expected_version, expected_start, expected_end
    from (values
        (50::bigint, 1::bigint, 'A', '2026-01-05 00:00Z', '{"direction":"south"}', 82000, 3, 50::bigint, null::bigint),
        (10, 1, 'A', '2026-01-01 00:00Z', '{"direction":"south"}', 80000, 1, 10, 30),
        (20, 1, 'A', '2026-01-02 00:00Z', '{"direction":"south"}', 82000, 1, 10, 30),
        (25, 1, 'A', '2026-01-02 00:00Z', '{"direction":"south"}', 82000, 1, 10, 30),
        (40, 1, 'A', '2026-01-04 00:00Z', '{"direction":"east"}', 82000, 2, 30, 50),
        (30, 1, 'A', '2026-01-03 00:00Z', '{"direction":"east"}', 82000, 2, 30, 50),
        (60, 1, 'B', '2026-01-01 00:00Z', '{"direction":null}', 70000, 1, 60, 61),
        (61, 1, 'B', '2026-01-01 00:00Z', '{"direction":"north"}', 70000, 2, 61, null),
        (70, 2, 'A', '2026-01-01 00:00Z', '{"direction":"east"}', 65000, 1, 70, null)
    ) v(task_id, source_id, code, ts, attrs, rent_jpy, expected_version, expected_start, expected_end)
), actual as (
    {{ suumo_listing_timeline('fixture') }}
)
select f.task_id
from fixture f full join actual a using (task_id)
where f.task_id is null or a.task_id is null
   or a.version_number is distinct from f.expected_version
   or a.effective_from_task_id is distinct from f.expected_start
   or a.effective_to_task_id is distinct from f.expected_end
   or a.is_current_version is distinct from (f.expected_end is null)
   or a.listing_version_key is distinct from
      md5(jsonb_build_array(f.source_id, f.suumo_property_code, f.expected_start)::text)
