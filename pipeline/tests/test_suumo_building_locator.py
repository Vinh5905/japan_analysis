"""Fixture-only protocol, matching, scheduling and orchestration checks."""

import json
import unittest
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from loaders import suumo_building_locator as geo
from vendor.google_maps import parse_search_response

NAME = "プレリスNEO大阪十三エルヴィオン"
OTHER = "セレニテ十三ミラク"
ADDRESS = "大阪府大阪市淀川区十三本町2丁目"
CANDIDATE = {
    "building_key": "key-a",
    "building_name_normalized": NAME,
    "building_address_query": ADDRESS,
}


def place(
    name=NAME,
    address="〒532-0024 大阪府大阪市淀川区十三本町２丁目１６−７",
    lat=34.7211494,
    lon=135.4785497,
    pid="ChIJ717DeADlAGARDQ_hxaRqu0U",
):
    return dict(
        name=name,
        address=address,
        latitude=lat,
        longitude=lon,
        place_id=pid,
        cid="5024727065188962061",
        maps_url="https://maps.google.com/?cid=5024727065188962061",
    )


def response(*places):
    return {
        "status": "ok",
        "candidates": list(places),
        "raw_response": {"body": "fixture"},
        "request_count": 1,
    }


def body(*places):
    records = []
    for p in places:
        record = [None] * 228
        record[2] = [p["address"]]
        record[9] = [None, None, p["latitude"], p["longitude"]]
        record[10] = "0x6000e50078c35eef:0x45bb6aa4c5e10f0d"
        record[11], record[78] = p["name"], p["place_id"]
        records.append(record)
    return ")]}'\n" + json.dumps(records, ensure_ascii=False)


def http(
    code=200, text=None, headers=None, url="https://www.google.com/search?tbm=map"
):
    return SimpleNamespace(
        status_code=code,
        text=text if text is not None else body(place()),
        url=url,
        headers=headers or {},
    )


class MatchingTests(unittest.TestCase):
    def test_protocol_and_point_order(self):
        parsed = parse_search_response(body(place()))
        result = geo.select_building_match(CANDIDATE, response(*parsed["candidates"]))
        self.assertEqual(result["status"], "matched")
        self.assertEqual(
            (result["latitude"], result["longitude"]), (34.7211494, 135.4785497)
        )
        self.assertEqual(result["building_full_address"], ADDRESS + "16-7")
        self.assertEqual(result["postal_code"], "532-0024")
        self.assertEqual(result["coordinate_level"], "building_poi")

    def test_nfkc_names_and_chome_only_numerals(self):
        candidate = {
            **CANDIDATE,
            "building_name_normalized": "　プレリスＮＥＯ大阪十三エルヴィオン ",
        }
        self.assertEqual(
            geo.build_building_query(candidate), geo.build_building_query(CANDIDATE)
        )
        self.assertEqual(
            geo.select_building_match(candidate, response(place()))["status"], "matched"
        )
        full = geo.parse_full_address(
            "大阪府大阪市淀川区東三国二丁目16番7号", "大阪府大阪市淀川区東三国2丁目"
        )
        self.assertEqual(
            full["building_full_address"], "大阪府大阪市淀川区東三国2丁目16-7"
        )
        self.assertEqual(
            geo.parse_full_address(ADDRESS + "16番地7号", ADDRESS)[
                "address_house_number"
            ],
            "7",
        )

    def test_real_buildings_same_chome_different_points(self):
        a = geo.select_building_match(CANDIDATE, response(place()))
        b = geo.select_building_match(
            {**CANDIDATE, "building_name_normalized": OTHER},
            response(
                place(OTHER, ADDRESS + "4-14", 34.7216039, 135.4800243, "other-place")
            ),
        )
        self.assertEqual(b["status"], "matched")
        self.assertNotEqual(a["google_place_id"], b["google_place_id"])
        self.assertNotEqual(
            (a["latitude"], a["longitude"]), (b["latitude"], b["longitude"])
        )

    def test_fake_name_wrong_suffix_address_and_area(self):
        fake = {
            **CANDIDATE,
            "building_name_normalized": "架空建物ZXQ9274存在しないマンション",
        }
        self.assertEqual(
            geo.select_building_match(fake, response(place("十三エステートハイツ")))[
                "status"
            ],
            "not_found",
        )
        for p in (
            place(NAME + "弐番館"),
            place(NAME + "1号棟"),
            place(NAME + "II"),
            place(address="大阪府大阪市淀川区十三本町1丁目16-7"),
            place(address=ADDRESS),
            place(address="大阪府大阪市淀川区十三本町"),
        ):
            r = geo.select_building_match(CANDIDATE, response(p))
            self.assertEqual(r["status"], "not_found")
            self.assertIsNone(r["latitude"])
        self.assertEqual(
            geo.select_building_match(CANDIDATE, response())["status"], "not_found"
        )
        for c in (
            {**CANDIDATE, "building_name_normalized": None},
            {**CANDIDATE, "building_address_query": None},
        ):
            self.assertIsNone(geo.build_building_query(c))
            self.assertEqual(
                geo.select_building_match(c, response(place()))["status"],
                "invalid_input",
            )

    def test_duplicate_and_ambiguous_places(self):
        self.assertEqual(
            geo.select_building_match(CANDIDATE, response(place(), place()))["status"],
            "matched",
        )
        for p in (
            place(pid="different-id"),
            place(lat=34.7212),
            place(address=ADDRESS + "17-8"),
        ):
            r = geo.select_building_match(CANDIDATE, response(place(), p))
            self.assertEqual(r["status"], "ambiguous")
            self.assertIsNone(r["latitude"])

    def test_invalid_coordinates_identity_and_json(self):
        for p in (
            place(lat=135.4, lon=34.7),
            place(lat=float("nan")),
            place(lon=float("inf")),
            place(lat=True),
            place(lat=0),
            place(pid=None),
        ):
            self.assertEqual(
                geo.select_building_match(CANDIDATE, response(p))["status"],
                "invalid_response",
            )
        for text in ("not json", ")]}'{}", ")]}'[NaN]", ")]}'[1e999]", ")]}'broken"):
            with self.assertRaises(ValueError):
                parse_search_response(text)


class HttpAndCacheTests(unittest.TestCase):
    def client(self, replies):
        session = Mock()
        session.get.side_effect = replies
        return geo.MapsSearchClient(
            session, sleep=Mock(), monotonic=Mock(return_value=0)
        ), session

    def test_success_is_single_tls_verified_request(self):
        client, session = self.client([http()])
        result = client.search(geo.build_building_query(CANDIDATE))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(session.get.call_count, 1)
        self.assertTrue(session.get.call_args.kwargs["verify"])
        self.assertEqual(session.get.call_args.kwargs["timeout"], 15)

    def test_timeout_5xx_retries_and_code_errors(self):
        for replies in (
            [TimeoutError("timeout")] * 3,
            [http(503)] * 3,
            [http(500), http(502), http()],
        ):
            client, session = self.client(replies)
            result = client.search("query")
            self.assertEqual(result["request_count"], 3)
            self.assertEqual(session.get.call_count, 3)
            self.assertIn(unittest.mock.call(2), client.sleep.call_args_list)
            self.assertIn(unittest.mock.call(4), client.sleep.call_args_list)
            self.assertIn(unittest.mock.call(3.0), client.sleep.call_args_list)
        client, _ = self.client([RuntimeError("programming bug")])
        with self.assertRaises(RuntimeError):
            client.search("query")

    def test_block_429_and_invalid_response_no_retry(self):
        for reply, status in (
            (http(429, headers={"Retry-After": "7200"}), "rate_limited"),
            (http(403), "blocked"),
            (http(text="captcha"), "blocked"),
            (http(url="https://consent.google.com/"), "blocked"),
            (http(text="HTML without JSON"), "invalid_response"),
        ):
            client, session = self.client([reply])
            result = client.search("query")
            self.assertEqual(result["status"], status)
            self.assertEqual(session.get.call_count, 1)
        now = geo.utcnow()
        from email.utils import format_datetime

        self.assertGreaterEqual(
            geo.retry_after_seconds(format_datetime(now + timedelta(hours=2)), now),
            7199,
        )
        self.assertLessEqual(
            geo.retry_after_seconds(format_datetime(now + timedelta(hours=2)), now),
            7200,
        )

    def test_schedule_and_failed_force_preserves_success(self):
        now = geo.utcnow()
        success = geo.merge_cached_result(
            None, geo.select_building_match(CANDIDATE, response(place())), now
        )
        self.assertFalse(geo.cache_is_due(success, now=now + timedelta(days=90)))
        self.assertTrue(geo.cache_is_due(success, force=True))
        for status, seconds in (
            ("not_found", 604800),
            ("request_error", 3600),
            ("blocked", 86400),
            ("rate_limited", 7200),
        ):
            failed = geo.merge_cached_result(
                None,
                geo.result_record(CANDIDATE, status, retry_after_seconds=7200),
                now,
            )
            self.assertEqual(
                (geo.as_datetime(failed["next_retry_at"]) - now).total_seconds(),
                seconds,
            )
            self.assertFalse(geo.cache_is_due(failed, now=now))
            self.assertTrue(
                geo.cache_is_due(failed, now=now + timedelta(seconds=seconds))
            )
        for status in ("invalid_input", "ambiguous", "invalid_response"):
            cached = geo.merge_cached_result(
                None, geo.result_record(CANDIDATE, status), now
            )
            self.assertFalse(geo.cache_is_due(cached, now=now + timedelta(days=99)))
        refreshed = geo.merge_cached_result(
            success, geo.result_record(CANDIDATE, "blocked"), now
        )
        for key in geo.ACCEPTED_FIELDS:
            self.assertEqual(refreshed[key], success[key])
        self.assertEqual(refreshed["status"], "matched")
        self.assertEqual(refreshed["last_attempt_status"], "blocked")
        self.assertEqual(refreshed["attempt_count"], 2)


class EnrichmentTests(unittest.TestCase):
    def run_enrichment(
        self,
        candidates,
        cached=None,
        cooldown=None,
        replies=None,
        worker_available=True,
        **kwargs,
    ):
        conn = MagicMock()
        conn.cursor.return_value.__enter__.return_value.fetchall.return_value = (
            candidates
        )
        context = Mock()
        context.__enter__ = Mock(return_value=conn)
        context.__exit__ = Mock(return_value=False)
        client = Mock()
        client.search.return_value = response(place())
        if replies is not None:
            client.search.side_effect = replies
        with (
            patch.object(geo, "postgres_connection", return_value=context),
            patch.object(geo, "acquire_provider_worker", return_value=worker_available),
            patch.object(geo, "read_cache", return_value=cached or {}),
            patch.object(geo, "provider_cooldown", return_value=cooldown),
            patch.object(geo, "write_cache_result") as write,
            patch.object(geo, "MapsSearchClient") as factory,
        ):
            result = geo.enrich_buildings(
                relation=geo.sql.Identifier("qa", "candidates"), client=client, **kwargs
            )
            return result, client, write, factory

    def test_cache_hit_and_dry_run(self):
        matched = geo.merge_cached_result(
            None, geo.select_building_match(CANDIDATE, response(place()))
        )
        summary, client, write, _ = self.run_enrichment(
            [CANDIDATE], {CANDIDATE["building_key"]: matched}
        )
        self.assertEqual(summary["cache_hits"], 1)
        client.search.assert_not_called()
        write.assert_not_called()
        summary, client, write, factory = self.run_enrichment([CANDIDATE], dry_run=True)
        self.assertEqual(summary["lookups"], 1)
        client.search.assert_not_called()
        write.assert_not_called()
        factory.assert_not_called()

    def test_limit_and_provider_cooldown_even_force(self):
        candidates = [{**CANDIDATE, "building_key": str(i)} for i in range(3)]
        summary, client, write, _ = self.run_enrichment(candidates, limit=1)
        self.assertEqual((summary["lookups"], summary["deferred"]), (1, 2))
        self.assertEqual(write.call_count, 1)
        summary, client, write, _ = self.run_enrichment(
            candidates, cooldown=geo.utcnow() + timedelta(hours=1), force=True
        )
        self.assertEqual(summary["deferred"], 3)
        client.search.assert_not_called()
        write.assert_not_called()
        summary, client, write, _ = self.run_enrichment(
            candidates, worker_available=False, force=True
        )
        self.assertEqual((summary["lookups"], summary["deferred"]), (0, 3))
        client.search.assert_not_called()
        write.assert_not_called()

    def test_block_stops_rest_and_database_code_errors_propagate(self):
        candidates = [{**CANDIDATE, "building_key": str(i)} for i in range(3)]
        summary, client, write, _ = self.run_enrichment(
            candidates,
            replies=[
                {
                    "status": "blocked",
                    "request_count": 1,
                    "raw_response": {"body": "captcha"},
                }
            ],
        )
        self.assertEqual(
            (summary["lookups"], summary["errors"], summary["deferred"]), (1, 1, 2)
        )
        self.assertEqual(client.search.call_count, 1)
        self.assertEqual(write.call_count, 1)
        with self.assertRaises(RuntimeError):
            self.run_enrichment([CANDIDATE], replies=[RuntimeError("code error")])
        with patch.object(
            geo, "postgres_connection", side_effect=RuntimeError("warehouse down")
        ):
            with self.assertRaises(RuntimeError):
                geo.enrich_buildings()


if __name__ == "__main__":
    unittest.main()
