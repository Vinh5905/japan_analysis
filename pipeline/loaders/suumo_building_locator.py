"""Building-name/chome lookup over HTTP; conservative matching, durable cache.

Coordinates describe a provider's building POI, not an independently verified
roofprint. No chome point is substituted for a missing building result.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)
from loaders.suumo_geocoder import canonical_address, clean_part, kanji_integer
from loaders.building_maps_http import MapsSearchClient, retry_after_seconds

PROVIDER = "google_maps_http"
QUERY_VERSION = "building_name_chome_v1"
MATCH_METHOD = "exact_name_chome_house_number"
ACCEPTED_FIELDS = (
    "building_full_address_raw",
    "building_full_address",
    "postal_code",
    "address_block",
    "address_house_number",
    "latitude",
    "longitude",
    "coordinate_level",
    "matched_address",
    "match_method",
    "google_place_id",
    "google_maps_url",
    "geocoded_at",
)
CACHE_COLUMNS = (
    "provider",
    "query_version",
    "building_key",
    "building_name_query",
    "address_query",
    "search_query",
    "status",
    *ACCEPTED_FIELDS,
    "raw_response",
    "attempt_count",
    "request_count",
    "last_attempted_at",
    "next_retry_at",
    "error_message",
    "last_attempt_status",
    "last_attempt_response",
)


def utcnow():
    return datetime.now(timezone.utc)


def normalized_name(value):
    return clean_part(value).lower()


def build_building_query(candidate):
    name = normalized_name(candidate.get("building_name_normalized"))
    address = canonical_address(candidate.get("building_address_query"))
    return f"{name} {address}" if name and re.search(r"[0-9]+丁目$", address) else None


def parse_full_address(raw, expected):
    """Normalize only chome numerals; keep locality names such as 東三国.

    Require known chome as an exact prefix and two additional address numbers.
    Do not guess building address from a postcode or POI viewport.
    """
    if not isinstance(raw, str):
        return None
    text = clean_part(raw)
    postal = re.match(r"^〒?([0-9]{3})[-−‐]?([0-9]{4})", text)
    postal_code = postal[1] + "-" + postal[2] if postal else None
    if postal:
        text = text[postal.end() :].lstrip(",、")
    match = re.search(r"([0-9〇零一二三四五六七八九十百千]+)丁目", text)
    if not match:
        return None
    text = (
        text[: match.start()]
        + str(kanji_integer(match[1]))
        + "丁目"
        + text[match.end() :]
    )
    expected = canonical_address(expected)
    if not text.startswith(expected):
        return None
    tail = text[len(expected) :]
    house = re.match(r"^([0-9]+)(?:番地?|[-−‐‑–—ー])([0-9]+)(?:号)?(?=$|[^0-9])", tail)
    if not house or int(house[1]) < 1 or int(house[2]) < 1:
        return None
    return {
        "building_full_address_raw": raw,
        "building_full_address": expected + house[1] + "-" + house[2],
        "postal_code": postal_code,
        "address_block": house[1],
        "address_house_number": house[2],
    }


def result_record(candidate, status, **extra):
    return {
        "provider": PROVIDER,
        "query_version": QUERY_VERSION,
        "building_key": candidate["building_key"],
        "building_name_query": candidate.get("building_name_normalized"),
        "address_query": candidate.get("building_address_query"),
        "search_query": build_building_query(candidate),
        "status": status,
        **dict.fromkeys(ACCEPTED_FIELDS),
        "raw_response": None,
        "error_message": None,
        "request_count": 0,
        **extra,
    }


def valid_point(latitude, longitude):
    return (
        all(
            isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
            for n in (latitude, longitude)
        )
        and 20 <= latitude <= 46
        and 122 <= longitude <= 154
    )


def select_building_match(candidate, response):
    audit = response.get("raw_response")
    if not build_building_query(candidate):
        return result_record(
            candidate,
            "invalid_input",
            raw_response=audit,
            error_message="Missing building name/chome",
        )
    if response["status"] != "ok":
        return result_record(
            candidate,
            response["status"],
            raw_response=audit,
            error_message=response.get("error_message"),
            retry_after_seconds=response.get("retry_after_seconds"),
            request_count=response.get("request_count", 0),
        )
    places = response.get("candidates")
    if not isinstance(places, list):
        return result_record(
            candidate,
            "invalid_response",
            raw_response=audit,
            error_message="Expected candidate list",
        )
    matches, invalid = {}, False
    for place in places:
        if not isinstance(place, dict):
            invalid = True
            continue
        if normalized_name(place.get("name")) != normalized_name(
            candidate["building_name_normalized"]
        ):
            continue
        address = parse_full_address(
            place.get("address"), candidate["building_address_query"]
        )
        if not address:
            continue
        lat, lon, pid = (
            place.get("latitude"),
            place.get("longitude"),
            place.get("place_id"),
        )
        if not valid_point(lat, lon) or not isinstance(pid, str) or not pid.strip():
            invalid = True
            continue
        key = (pid, address["building_full_address"], float(lat), float(lon))
        matches[key] = {
            **address,
            "latitude": float(lat),
            "longitude": float(lon),
            "google_place_id": pid,
            "google_maps_url": place.get("maps_url"),
            "matched_address": place["address"],
        }
    extra = {"raw_response": audit, "request_count": response.get("request_count", 0)}
    if invalid:
        return result_record(
            candidate,
            "invalid_response",
            error_message="Malformed matching place or invalid point/Place ID",
            **extra,
        )
    if len(matches) > 1:
        return result_record(
            candidate,
            "ambiguous",
            error_message="Multiple matching place identities/addresses/points",
            **extra,
        )
    if not matches:
        return result_record(
            candidate,
            "not_found",
            error_message="No exact name, chome and house-number match",
            **extra,
        )
    return result_record(
        candidate,
        "matched",
        **next(iter(matches.values())),
        coordinate_level="building_poi",
        match_method=MATCH_METHOD,
        geocoded_at=utcnow().isoformat(),
        **extra,
    )


class MapsHttpWorkerClient:
    """Keep curl_cffi/cffi out of the Airflow dependency environment."""

    def __init__(self, executable):
        self.executable, self.last_finished = executable, None

    def search(self, query):
        if self.last_finished is not None:
            time.sleep(max(0, 3.0 - (time.monotonic() - self.last_finished)))
        run = subprocess.run(
            [self.executable, "-m", "loaders.building_maps_http"],
            input=json.dumps({"query": query}),
            text=True,
            capture_output=True,
            timeout=90,
        )
        self.last_finished = time.monotonic()
        if run.returncode:
            raise RuntimeError(
                f"HTTP worker failed with exit {run.returncode}: {run.stderr[-1500:]}"
            )
        result = json.loads(run.stdout)
        if not isinstance(result, dict) or "status" not in result:
            raise RuntimeError("Invalid HTTP worker result")
        return result

    def close(self):
        pass


def make_client():
    executable = os.getenv("SUUMO_BUILDING_HTTP_PYTHON")
    return MapsHttpWorkerClient(executable) if executable else MapsSearchClient()


def search_building(query, client=None):
    if client is not None:
        return client.search(query)
    owned = make_client()
    try:
        return owned.search(query)
    finally:
        owned.close()


def as_datetime(value):
    return datetime.fromisoformat(value) if isinstance(value, str) else value


def cache_is_due(cached, *, force=False, now=None):
    if cached is None or force:
        return True
    return (
        cached["status"] != "matched"
        and cached.get("next_retry_at") is not None
        and as_datetime(cached["next_retry_at"]) <= (now or utcnow())
    )


def merge_cached_result(previous, result, now=None):
    now = now or utcnow()
    status = result["status"]
    delay = {
        "not_found": 7 * 86400,
        "request_error": 3600,
        "blocked": 86400,
        "rate_limited": max(3600, result.get("retry_after_seconds") or 0),
    }.get(status)
    audit = {
        "attempt_count": (previous or {}).get("attempt_count", 0) + 1,
        "request_count": (previous or {}).get("request_count", 0)
        + result.get("request_count", 0),
        "last_attempted_at": now.isoformat(),
        "next_retry_at": (now + timedelta(seconds=delay)).isoformat()
        if delay
        else None,
        "last_attempt_status": status,
        "last_attempt_response": result.get("raw_response"),
    }
    if previous and previous["status"] == "matched" and status != "matched":
        return {
            **previous,
            **audit,
            "error_message": "Refresh "
            + status
            + ": "
            + (result.get("error_message") or ""),
        }
    return {**result, **audit}


def ensure_cache_table(config=None):
    path = (
        Path(__file__).resolve().parents[1] / "warehouse/suumo_building_locations.sql"
    )
    with postgres_connection(config or load_warehouse_postgres_config()) as connection:
        connection.execute(path.read_text())


def candidate_relation():
    project = Path(
        os.getenv(
            "DBT_PROJECT_DIR",
            str(Path(__file__).resolve().parents[2] / "analytics/dbt"),
        )
    )
    node = json.loads((project / "target/airflow/manifest.json").read_text())["nodes"][
        "model.japan_analysis.int_suumo__building_lookup_candidates"
    ]
    return sql.Identifier(node["schema"], node["alias"])


def read_cache(connection):
    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "select * from raw.suumo_building_locations where provider=%s and query_version=%s",
            (PROVIDER, QUERY_VERSION),
        )
        return {r["building_key"]: dict(r) for r in cursor.fetchall()}


def provider_cooldown(connection):
    # Read all versions: changing matching rules must not bypass a provider block.
    return connection.execute(
        "select max(next_retry_at) from raw.suumo_building_locations where provider=%s and last_attempt_status in ('blocked','rate_limited')",
        (PROVIDER,),
    ).fetchone()[0]


def acquire_provider_worker(connection):
    # Session lock survives per-address commits and is released on disconnect.
    # Includes all rule versions and manual CLI invocations of this provider.
    return connection.execute(
        "select pg_try_advisory_lock(hashtextextended('suumo_building_locator:' || %s, 0))",
        (PROVIDER,),
    ).fetchone()[0]


def write_cache_result(connection, result):
    values = [
        Jsonb(result.get(c))
        if c in ("raw_response", "last_attempt_response")
        else result.get(c)
        for c in CACHE_COLUMNS
    ]
    updates = [
        sql.SQL("{}=EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
        for c in CACHE_COLUMNS[3:]
    ]
    connection.execute(
        sql.SQL(
            "insert into raw.suumo_building_locations ({}) values ({}) on conflict (provider,query_version,building_key) do update set {}"
        ).format(
            sql.SQL(",").join(map(sql.Identifier, CACHE_COLUMNS)),
            sql.SQL(",").join(sql.Placeholder() for _ in CACHE_COLUMNS),
            sql.SQL(",").join(updates),
        ),
        values,
    )
    connection.commit()


def enrich_buildings(
    *, config=None, relation=None, limit=None, dry_run=False, force=False, client=None
):
    limit = (
        int(os.getenv("SUUMO_BUILDING_LOOKUP_LIMIT", "30")) if limit is None else limit
    )
    if limit < 1:
        raise ValueError("limit must be positive")
    summary = dict.fromkeys(
        (
            "candidates",
            "new_buildings",
            "cache_hits",
            "lookups",
            "matched",
            "unmatched",
            "deferred",
            "errors",
            "request_count",
        ),
        0,
    )
    summary["dry_run"] = dry_run
    owned = None
    with postgres_connection(config or load_warehouse_postgres_config()) as connection:
        worker_available = dry_run or acquire_provider_worker(connection)
        cached = read_cache(connection)
        cooldown = provider_cooldown(connection)
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                sql.SQL("select * from {} order by building_key").format(
                    relation or candidate_relation()
                )
            )
            candidates = list(cursor.fetchall())
        summary["candidates"] = len(candidates)
        try:
            for candidate in candidates:
                previous = cached.get(candidate["building_key"])
                if not cache_is_due(previous, force=force):
                    summary[
                        "cache_hits" if previous["status"] == "matched" else "deferred"
                    ] += 1
                    continue
                if (
                    not worker_available
                    or (cooldown and as_datetime(cooldown) > utcnow())
                    or summary["lookups"] >= limit
                ):
                    summary["deferred"] += 1
                    continue
                summary["new_buildings"] += previous is None
                summary["lookups"] += 1
                if dry_run:
                    continue
                query = build_building_query(candidate)
                if query is None:
                    result = result_record(
                        candidate,
                        "invalid_input",
                        error_message="Missing building name/chome",
                    )
                else:
                    if client is None and owned is None:
                        owned = make_client()
                    result = select_building_match(
                        candidate, search_building(query, client or owned)
                    )
                merged = merge_cached_result(previous, result)
                write_cache_result(connection, merged)
                cached[candidate["building_key"]] = merged
                summary["request_count"] += result.get("request_count", 0)
                summary["matched"] += result["status"] == "matched"
                summary["unmatched"] += result["status"] in ("not_found", "ambiguous")
                summary["errors"] += result["status"] in (
                    "invalid_input",
                    "invalid_response",
                    "request_error",
                    "blocked",
                    "rate_limited",
                )
                if result["status"] in ("blocked", "rate_limited"):
                    cooldown = merged["next_retry_at"]
        finally:
            if owned is not None:
                owned.close()
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true", help="Read-only; no DDL, writes or HTTP"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh eligible entries; never bypass provider cooldown",
    )
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.init_only and args.dry_run:
        parser.error("--init-only and --dry-run cannot be combined")
    if not args.dry_run:
        ensure_cache_table()
    if args.init_only:
        print(json.dumps({"initialized": True}))
    else:
        print(
            json.dumps(
                enrich_buildings(
                    limit=args.limit, dry_run=args.dry_run, force=args.force
                )
            )
        )


if __name__ == "__main__":
    main()
