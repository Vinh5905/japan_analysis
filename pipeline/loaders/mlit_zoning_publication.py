"""Immutable zoning runs, quality review, atomic publication and pinned exports."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg.pq import TransactionStatus

from loaders.mlit_zoning_loader import canonical, digest
from loaders.suumo_batch_loader import (
    load_warehouse_postgres_config,
    postgres_connection,
)

MATCHING_VERSION = "postgis_covers_10m_v1"


def connection():
    return postgres_connection(load_warehouse_postgres_config())


def prepare_run(dataset_key=None, city_code="27100"):
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        # REPEATABLE READ makes input rows/task manifest a coherent snapshot.
        if conn.info.transaction_status == TransactionStatus.IDLE:
            cur.execute("set transaction isolation level repeatable read")
        cur.execute(
            "select pg_advisory_xact_lock(hashtext(%s))", ("mlit_prepare_" + city_code,)
        )
        if dataset_key is None:
            cur.execute(
                """
                SELECT dataset_key
                FROM raw.mlit_datasets
                WHERE city_code = %s
                ORDER BY last_checked_at DESC, dataset_key
                LIMIT 1
                """,
                (city_code,),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("No MLIT source available; refresh_source first")
            dataset_key = row["dataset_key"]
        cur.execute(
            "select city_code from raw.mlit_datasets where dataset_key=%s",
            (dataset_key,),
        )
        row = cur.fetchone()
        if not row or row["city_code"] != city_code:
            raise ValueError("Dataset scope mismatch")
        cur.execute(
            """
            SELECT *
            FROM intermediate.int_suumo__zoning_inputs
            ORDER BY building_key
            """
        )
        inputs = list(cur.fetchall())
        cur.execute("""
        SELECT
            e.task_id,
            e.building_key,
            coalesce(r.data_hash, s.data_hash) AS data_hash
        FROM intermediate.int_suumo__building_events e
        LEFT JOIN raw.suumo_parser_records r USING (task_id)
        LEFT JOIN raw.suumo_parser_records_seed s USING (task_id)
        ORDER BY e.task_id
        """)
        tasks = list(cur.fetchall())
        fingerprint = digest({"locations": inputs, "tasks": tasks})
        run_id = digest([dataset_key, MATCHING_VERSION, fingerprint])
        cur.execute(
            """
            SELECT
                run_id,
                status,
                publication_sequence
            FROM enrichment.zoning_runs
            WHERE run_id = %s
            """,
            (run_id,),
        )
        old = cur.fetchone()
        if old:
            return {
                **old,
                "dataset_key": dataset_key,
                "reused": True,
                "inputs": len(inputs),
            }
        cur.execute(
            """
            INSERT INTO enrichment.zoning_runs (
                run_id, dataset_key, city_code, matching_version, input_fingerprint
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, dataset_key, city_code, MATCHING_VERSION, fingerprint),
        )
        cur.executemany(
            """
            INSERT INTO enrichment.zoning_run_inputs
            (
                run_id,
                building_key,
                building_name,
                address_query,
                geography_key,
                latitude,
                longitude,
                location_status,
                coordinate_level,
                provider,
                place_id,
                location_fingerprint
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    run_id,
                    *[
                        i[k]
                        for k in (
                            "building_key",
                            "building_name",
                            "address_query",
                            "geography_key",
                            "latitude",
                            "longitude",
                            "location_status",
                            "coordinate_level",
                            "provider",
                            "place_id",
                            "location_fingerprint",
                        )
                    ],
                )
                for i in inputs
            ],
        )
        cur.executemany(
            "insert into enrichment.zoning_run_tasks values (%s,%s,%s,%s)",
            [(run_id, t["task_id"], t["building_key"], t["data_hash"]) for t in tasks],
        )
        return {
            "run_id": run_id,
            "dataset_key": dataset_key,
            "reused": False,
            "inputs": len(inputs),
        }


def review_run(conn, run_id):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("select * from enrichment.zoning_runs where run_id=%s", (run_id,))
        run = cur.fetchone()
        if not run:
            raise ValueError("Unknown run")
        cur.execute(
            """
            SELECT count(*) AS bad
            FROM intermediate.int_mlit__polygon_states
            WHERE
                dataset_key = %s
                AND (
                    NOT geometry_valid
                    OR attribute_quality <> 'valid'
                    OR zoning_code IS null
                    OR zoning_name IS null
                )
            """,
            (run["dataset_key"],),
        )
        if cur.fetchone()["bad"]:
            raise RuntimeError(
                "Invalid geometry/attributes; publication cannot be overridden"
            )
        cur.execute(
            """
            SELECT
                d.feature_count,
                (
                    SELECT count(*)
                    FROM raw.mlit_zoning_polygons p
                    WHERE p.dataset_key = d.dataset_key
                ) AS raw_count,
                (
                    SELECT count(*)
                    FROM intermediate.int_mlit__polygon_states p
                    WHERE p.dataset_key = d.dataset_key
                ) AS normalized_count
            FROM raw.mlit_datasets d
            WHERE dataset_key = %s
            """,
            (run["dataset_key"],),
        )
        counts = cur.fetchone()
        if not (
            counts["feature_count"] == counts["raw_count"] == counts["normalized_count"]
        ):
            raise RuntimeError(
                "Incomplete MLIT dataset normalization; "
                "publication cannot be overridden"
            )
        cur.execute(
            """select count(*) as n from enrichment.zoning_run_inputs where run_id=%s""",
            (run_id,),
        )
        n = cur.fetchone()["n"]
        cur.execute(
            """
            SELECT
                count(*) AS n,
                count(DISTINCT building_key) AS u
            FROM intermediate.int_mlit__zoning_matches
            WHERE run_id = %s
            """,
            (run_id,),
        )
        counts = cur.fetchone()
        if n != counts["n"] or n != counts["u"]:
            raise RuntimeError("Incomplete/duplicate spatial results")
        cur.execute(
            """
            SELECT count(*) AS n
            FROM enrichment.zoning_run_inputs i
            FULL JOIN
                (
                    SELECT *
                    FROM intermediate.int_mlit__zoning_matches
                    WHERE run_id = %s
                ) m
                USING (run_id, building_key)
            WHERE
                (i.run_id = %s OR m.run_id = %s)
                AND (
                    i.building_key IS null
                    OR m.building_key IS null
                    OR i.location_fingerprint <> m.location_fingerprint
                    OR (
                        m.zoning_status = 'matched'
                        AND (
                            m.polygon_count <> 1
                            OR m.boundary_distance_m IS null
                            OR m.boundary_distance_m < 10
                            OR i.location_status IS DISTINCT FROM 'matched'
                            OR i.coordinate_level IS DISTINCT FROM 'building_poi'
                            OR i.latitude IS null
                            OR i.longitude IS null
                            OR i.latitude NOT BETWEEN 20
                            AND 46
                            OR i.longitude NOT BETWEEN 122
                            AND 154
                        )
                    )
                    OR (
                        m.zoning_status <> 'matched'
                        AND (
                            m.zoning_code IS NOT null
                            OR m.zoning_name IS NOT null
                            OR m.far_pct IS NOT null
                            OR m.bcr_pct IS NOT null
                        )
                    )
                )
            """,
            (run_id, run_id, run_id),
        )
        if cur.fetchone()["n"]:
            raise RuntimeError("Match integrity failure")
        cur.execute(
            """
            SELECT run_id
            FROM enrichment.zoning_publication_pointer
            WHERE city_code = %s
            """,
            (run["city_code"],),
        )
        row = cur.fetchone()
        previous = row["run_id"] if row else None
        regressions = []
        if previous and previous != run_id:
            cur.execute(
                """
                SELECT
                    o.building_key,
                    to_jsonb(o) AS before,
                    to_jsonb(n) AS after
                FROM intermediate.int_mlit__published_results o
                LEFT JOIN
                    intermediate.int_mlit__zoning_matches n
                    ON
                        n.run_id = %s
                        AND n.building_key = o.building_key
                WHERE
                    o.run_id = %s
                    AND o.zoning_status = 'matched'
                    AND (
                        n.zoning_status IS DISTINCT FROM 'matched'
                        OR (o.zoning_code IS NOT null AND n.zoning_code IS null)
                        OR (o.zoning_name IS NOT null AND n.zoning_name IS null)
                        OR (o.far_pct IS NOT null AND n.far_pct IS null)
                        OR (o.bcr_pct IS NOT null AND n.bcr_pct IS null)
                    )
                """,
                (run_id, previous),
            )
            regressions = list(cur.fetchall())
            # Removed candidates cannot be accepted silently:
            # no per-building result exists.
            if any(r["after"] is None for r in regressions):
                raise RuntimeError(
                    "Published building missing from candidate snapshot; "
                    "input must retain it"
                )
        return run, {
            "previous_run_id": previous,
            "regressions": regressions,
            "input_count": n,
        }


def check_run(run_id):
    with connection() as conn:
        run, report = review_run(conn, run_id)
        conn.execute(
            """
            UPDATE raw.mlit_datasets SET validation_status = 'validated'
            WHERE dataset_key = %s
            """,
            (run["dataset_key"],),
        )
        if run["publication_sequence"] is None:
            conn.execute(
                """
                UPDATE
                    enrichment.zoning_runs SET
                    quality_checked_at = now(), quality_passed = true,
                    review = %s, status = %s
                WHERE run_id = %s
                """,
                (
                    Jsonb(report),
                    "blocked" if report["regressions"] else "evaluated",
                    run_id,
                ),
            )
        return report


def publish_run(
    run_id, *, accept_null=(), reason="Automatic quality-approved publication"
):
    if accept_null and (
        not reason
        or not reason.strip()
        or reason == "Automatic quality-approved publication"
    ):
        raise ValueError("Explicit reason required for accepted NULL buildings")
    with connection() as conn:
        conn.execute("select pg_advisory_xact_lock(hashtext('mlit_publication'))")
        run, report = review_run(conn, run_id)
        if not run["quality_passed"]:
            raise RuntimeError(
                "Run must pass dbt build/tests and check before publication"
            )
        if report["previous_run_id"] == run_id:
            return {"run_id": run_id, "reused": True}
        needed = {r["building_key"] for r in report["regressions"]}
        if set(accept_null) != needed:
            if not accept_null and needed:
                conn.execute(
                    """
                    UPDATE enrichment.zoning_runs SET status = 'blocked', review = %s
                    WHERE run_id = %s
                    """,
                    (Jsonb(report), run_id),
                )
                return {
                    "run_id": run_id,
                    "published": False,
                    "blocked_buildings": sorted(needed),
                }
            raise ValueError("Accept-NULL list must exactly cover reviewed regressions")
        if run["publication_sequence"] is not None:
            raise ValueError(
                "Already-published run must be activated through rollback, "
                "not republished"
            )
        conn.execute(
            """
            UPDATE enrichment.zoning_runs SET
                status = 'published',
                publication_sequence
                = nextval('enrichment.zoning_publication_sequence'),
                published_at = clock_timestamp()
            WHERE run_id = %s
            """,
            (run_id,),
        )
        conn.execute(
            """
            INSERT INTO enrichment.zoning_publication_pointer VALUES (%s, %s)
            ON CONFLICT (city_code) DO UPDATE SET run_id = excluded.run_id
            """,
            (run["city_code"], run_id),
        )
        conn.execute(
            """
            INSERT INTO enrichment.zoning_publication_audit
            (
                city_code,
                previous_run_id,
                run_id,
                action,
                reason,
                accepted_null_buildings
            ) VALUES (%s, %s, %s, 'publish', %s, %s)
            """,
            (
                run["city_code"],
                report["previous_run_id"],
                run_id,
                reason,
                Jsonb(sorted(accept_null)),
            ),
        )
        return {
            "run_id": run_id,
            "published": True,
            "accepted_null": sorted(accept_null),
        }


def rollback_run(run_id, reason):
    if not reason or not reason.strip():
        raise ValueError("Rollback reason required")
    with connection() as conn:
        conn.execute("select pg_advisory_xact_lock(hashtext('mlit_publication'))")
        row = conn.execute(
            """
            SELECT city_code
            FROM enrichment.zoning_runs
            WHERE run_id = %s AND publication_sequence IS NOT null
            """,
            (run_id,),
        ).fetchone()
        if not row:
            raise ValueError("Rollback target must be a published run")
        city = row[0]
        old = conn.execute(
            """
            SELECT run_id
            FROM enrichment.zoning_publication_pointer
            WHERE city_code = %s
            """,
            (city,),
        ).fetchone()
        conn.execute(
            """
            UPDATE enrichment.zoning_publication_pointer SET run_id = %s
            WHERE city_code = %s
            """,
            (run_id, city),
        )
        conn.execute(
            """
            INSERT INTO enrichment.zoning_publication_audit
            (city_code, previous_run_id, run_id, action, reason) VALUES (
                %s, %s, %s, 'rollback', %s
            )
            """,
            (city, old[0], run_id, reason),
        )
    return {"active_run_id": run_id, "action": "rollback"}


def export_run(run_id, destination):
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=True)
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        if conn.info.transaction_status == TransactionStatus.IDLE:
            cur.execute("set transaction isolation level repeatable read")
        cur.execute(
            """
            SELECT
                to_jsonb(r) AS run,
                to_jsonb(d) AS dataset
            FROM enrichment.zoning_runs r
            JOIN raw.mlit_datasets d USING (dataset_key)
            WHERE r.run_id = %s AND r.publication_sequence IS NOT null
            """,
            (run_id,),
        )
        manifest = cur.fetchone()
        if not manifest:
            raise ValueError("Export requires a published run")
        for filename, query in [
            (
                "building_inputs.csv",
                """
                SELECT *
                FROM enrichment.zoning_run_inputs
                WHERE run_id = %s
                ORDER BY building_key
                """,
            ),
            (
                "matches.csv",
                """
                SELECT *
                FROM intermediate.int_mlit__published_results
                WHERE run_id = %s
                ORDER BY building_key
                """,
            ),
            (
                "tasks.csv",
                """
                SELECT *
                FROM enrichment.zoning_run_tasks
                WHERE run_id = %s
                ORDER BY task_id
                """,
            ),
            (
                "observations.csv",
                """
                SELECT
                    o.*,
                    m.zoning_status,
                    m.zoning_code,
                    m.zoning_name,
                    m.far_pct,
                    m.bcr_pct,
                    m.boundary_distance_m,
                    m.run_id AS zoning_publication_run_id,
                    m.dataset_key AS zoning_dataset_key,
                    i.latitude AS zoning_input_latitude,
                    i.longitude AS zoning_input_longitude,
                    i.provider AS zoning_input_provider,
                    i.place_id AS zoning_input_place_id,
                    t.building_key AS snapshot_building_key
                FROM enrichment.zoning_run_tasks t
                JOIN mart.rental_price_observations o USING (task_id)
                LEFT JOIN
                    intermediate.int_mlit__published_results m
                    ON
                        m.run_id = t.run_id
                        AND m.building_key = t.building_key
                LEFT JOIN
                    enrichment.zoning_run_inputs i
                    ON
                        i.run_id = t.run_id
                        AND i.building_key = t.building_key
                WHERE t.run_id = %s
                ORDER BY o.task_id
                """,
            ),
        ]:
            cur.execute(query, (run_id,))
            with (out / filename).open("w", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=[c.name for c in cur.description]
                )
                writer.writeheader()
                writer.writerows(cur)
        manifest["export_sha256"] = {
            p.name: digest(p.read_bytes()) for p in out.glob("*.csv")
        }
        manifest["semantics"] = (
            "Publication-time planning attributes, "
            "not historical zoning on observation date. "
            "Building coordinates are provider POIs."
        )
        (out / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, default=str)
        )
    return {"run_id": run_id, "path": str(out)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "action", choices=["prepare", "check", "publish", "rollback", "export"]
    )
    p.add_argument("--run-id")
    p.add_argument("--dataset-key")
    p.add_argument("--reason")
    p.add_argument("--accept-null", action="append", default=[])
    p.add_argument("--output")
    args = p.parse_args()
    if args.action == "prepare":
        result = prepare_run(args.dataset_key)
    else:
        if not args.run_id:
            p.error("--run-id required")
        if args.action == "check":
            result = check_run(args.run_id)
        elif args.action == "publish":
            result = publish_run(
                args.run_id,
                accept_null=args.accept_null,
                reason=args.reason or "Automatic quality-approved publication",
            )
        elif args.action == "rollback":
            result = rollback_run(args.run_id, args.reason)
        else:
            if not args.output:
                p.error("--output required")
            result = export_run(args.run_id, args.output)
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
