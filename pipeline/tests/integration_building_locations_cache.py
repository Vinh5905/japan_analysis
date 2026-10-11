"""Local PostgreSQL cache checks; fixture-only, all writes rolled back.

Run after building-location-init. Uses the real constraints/upsert/cooldown
queries without modifying committed cache data or calling any provider.
"""

from types import SimpleNamespace
from uuid import uuid4

from psycopg.errors import CheckViolation
from psycopg.rows import dict_row

from loaders import suumo_building_locator as geo


def main():
    candidate = {
        "building_key": "qa-" + uuid4().hex,
        "building_name_normalized": "プレリスNEO大阪十三エルヴィオン",
        "building_address_query": "大阪府大阪市淀川区十三本町2丁目",
    }
    fixture = {
        "status": "ok",
        "request_count": 1,
        "raw_response": {"fixture": True},
        "candidates": [
            {
                "name": candidate["building_name_normalized"],
                "address": "〒532-0024 大阪府大阪市淀川区十三本町2丁目16-7",
                "latitude": 34.7211494,
                "longitude": 135.4785497,
                "place_id": "qa-place-id",
                "maps_url": "https://maps.google.com/?cid=1",
            }
        ],
    }
    with geo.postgres_connection(geo.load_warehouse_postgres_config()) as conn:
        # The loader normally commits each address. Suppress commits only in QA
        # so every fixture write remains invisible outside this transaction.
        writer = SimpleNamespace(execute=conn.execute, commit=lambda: None)
        try:
            assert geo.acquire_provider_worker(conn)
            with geo.postgres_connection(geo.load_warehouse_postgres_config()) as other:
                assert not geo.acquire_provider_worker(other), (
                    "Two provider workers acquired the same lock"
                )
            result = geo.merge_cached_result(
                None, geo.select_building_match(candidate, fixture)
            )
            geo.write_cache_result(writer, result)
            geo.write_cache_result(writer, result)
            rows = conn.execute(
                "select count(*) from raw.suumo_building_locations where building_key=%s",
                (candidate["building_key"],),
            ).fetchone()[0]
            assert rows == 1, "Upsert duplicated the cache key"
            previous = (
                conn.cursor(row_factory=dict_row)
                .execute(
                    "select * from raw.suumo_building_locations where building_key=%s",
                    (candidate["building_key"],),
                )
                .fetchone()
            )
            failed = geo.merge_cached_result(
                previous,
                geo.result_record(
                    candidate,
                    "blocked",
                    error_message="fixture CAPTCHA",
                    raw_response={"fixture": "blocked"},
                ),
            )
            geo.write_cache_result(writer, failed)
            saved = geo.read_cache(conn)[candidate["building_key"]]
            assert (
                saved["status"] == "matched"
                and saved["last_attempt_status"] == "blocked"
            )
            assert all(saved[key] == previous[key] for key in geo.ACCEPTED_FIELDS)
            assert geo.provider_cooldown(conn) >= geo.as_datetime(
                failed["next_retry_at"]
            )
            # A different matching version still blocks the whole provider.
            foreign = {
                **failed,
                "query_version": "qa-other-version",
                "next_retry_at": (geo.utcnow() + geo.timedelta(days=2)).isoformat(),
            }
            geo.write_cache_result(writer, foreign)
            assert (
                geo.read_cache(conn)[candidate["building_key"]]["next_retry_at"]
                == saved["next_retry_at"]
            )
            assert geo.provider_cooldown(conn) >= geo.as_datetime(
                foreign["next_retry_at"]
            )
            for changes in (
                {"latitude": None},
                {"longitude": 34.7},
                {"coordinate_level": None},
                {"coordinate_level": "chome"},
            ):
                try:
                    with conn.transaction():
                        geo.write_cache_result(writer, {**failed, **changes})
                except CheckViolation:
                    pass
                else:
                    raise AssertionError(
                        "Cache accepted invalid matched metadata: " + str(changes)
                    )
        finally:
            conn.rollback()
        assert (
            conn.execute(
                "select count(*) from raw.suumo_building_locations where building_key=%s",
                (candidate["building_key"],),
            ).fetchone()[0]
            == 0
        )
    print(
        "QA PASS cache upsert, refresh preservation, cooldown and constraints; all fixture writes rolled back"
    )


if __name__ == "__main__":
    main()
