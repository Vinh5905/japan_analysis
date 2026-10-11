"""Real PostGIS and publication fixtures; all warehouse writes roll back."""

from __future__ import annotations
import json
import re
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from psycopg import sql
from psycopg.types.json import Jsonb
from loaders import mlit_zoning_publication as p


def clone(conn, table, overrides, where="true"):
    conn.execute(
        sql.SQL(
            "insert into {} select (jsonb_populate_record(null::{},to_jsonb(x)||%s)).* from {} x where "
            + where
            + " limit 1"
        ).format(*[sql.SQL(table)] * 3),
        (Jsonb(overrides),),
    )


def fixture_dataset(conn, key):
    clone(
        conn,
        "raw.mlit_datasets",
        {
            "dataset_key": key,
            "zip_sha256": key,
            "city_metadata_sha256": key,
            "city_code": "fixture",
            "feature_count": 1,
        },
    )
    original = conn.execute(
        "select dataset_key,source_file,feature_ordinal from intermediate.int_mlit__polygon_states where not ST_Covers(geom,ST_SetSRID(ST_MakePoint(135.5,34.7),6668)) limit 1"
    ).fetchone()
    where = (
        "dataset_key='"
        + original[0]
        + "' and source_file='"
        + original[1]
        + "' and feature_ordinal="
        + str(original[2])
    )
    clone(conn, "raw.mlit_zoning_polygons", {"dataset_key": key}, where)
    clone(conn, "intermediate.int_mlit__polygon_states", {"dataset_key": key}, where)


def fixture_run(
    conn, run_id, dataset_key, building="fixture_building", status="matched", far=400
):
    conn.execute(
        """insert into enrichment.zoning_runs(run_id,dataset_key,city_code,matching_version,input_fingerprint)
      values (%s,%s,'fixture','fixture',%s)""",
        (run_id, dataset_key, run_id),
    )
    conn.execute(
        """insert into enrichment.zoning_run_inputs(run_id,building_key,location_fingerprint,latitude,longitude,location_status,coordinate_level)
      values (%s,%s,'fixture_location',34.73,135.49,'matched','building_poi')""",
        (run_id, building),
    )
    clone(
        conn,
        "intermediate.int_mlit__zoning_matches",
        {
            "run_id": run_id,
            "dataset_key": dataset_key,
            "building_key": building,
            "location_fingerprint": "fixture_location",
            "zoning_status": status,
            "far_pct": far if status == "matched" else None,
            "zoning_code": "10" if status == "matched" else None,
            "zoning_name": "商業地域" if status == "matched" else None,
            "bcr_pct": 80 if status == "matched" else None,
            "polygon_count": 1,
            "boundary_distance_m": 20 if status == "matched" else 5,
        },
    )


def main():
    conn = p.connection()
    conn.execute("set transaction isolation level repeatable read")

    @contextmanager
    def fixture_connection():
        yield conn

    try:
        with patch.object(p, "connection", fixture_connection):
            # One independent fixture dataset, city pointer and building.
            fixture_dataset(conn, "fixture_dataset")
            fixture_run(conn, "fixture_a", "fixture_dataset")
            p.check_run("fixture_a")
            assert p.publish_run("fixture_a")["published"]
            first = conn.execute(
                "select building_zoning_version_key from mart.bridge_building_zoning where building_key='fixture_building'"
            ).fetchone()[0]
            fixture_dataset(conn, "fixture_dataset2")
            fixture_run(conn, "fixture_same", "fixture_dataset2")
            p.check_run("fixture_same")
            p.publish_run("fixture_same")
            assert conn.execute(
                "select count(*),min(building_zoning_version_key) from mart.bridge_building_zoning where building_key='fixture_building'"
            ).fetchone() == (1, first)
            fixture_run(conn, "fixture_b", "fixture_dataset2", far=600)
            p.check_run("fixture_b")
            p.publish_run("fixture_b")
            fixture_run(conn, "fixture_back_a", "fixture_dataset2", far=400)
            p.check_run("fixture_back_a")
            p.publish_run("fixture_back_a")
            versions = conn.execute(
                "select far_pct,version_number,is_current from mart.bridge_building_zoning where building_key='fixture_building' order by version_number"
            ).fetchall()
            assert versions == [(400, 1, False), (600, 2, False), (400, 3, True)], (
                versions
            )
            fixture_run(conn, "fixture_lost_far", "fixture_dataset2", far=None)
            assert len(p.check_run("fixture_lost_far")["regressions"]) == 1
            assert not p.publish_run("fixture_lost_far")["published"]
            fixture_run(conn, "fixture_bad", "fixture_dataset2", status="near_boundary")
            report = p.check_run("fixture_bad")
            assert len(report["regressions"]) == 1
            assert not p.publish_run("fixture_bad")["published"]
            assert (
                conn.execute(
                    "select run_id from enrichment.zoning_publication_pointer where city_code='fixture'"
                ).fetchone()[0]
                == "fixture_back_a"
            )
            assert (
                conn.execute(
                    "select count(*) from mart.bridge_building_zoning where building_key='fixture_building'"
                ).fetchone()[0]
                == 3
            )
            with conn.transaction():
                try:
                    p.publish_run("fixture_bad", accept_null=["fixture_building"])
                except ValueError:
                    pass
                else:
                    raise AssertionError("Missing explicit reason accepted")
            assert p.publish_run(
                "fixture_bad",
                accept_null=["fixture_building"],
                reason="Reviewed boundary fixture",
            )["published"]
            assert conn.execute(
                "select zoning_status,far_pct,bcr_pct,zoning_name from intermediate.int_mlit__published_results where run_id='fixture_bad'"
            ).fetchone() == ("accepted_null", None, None, None)
            p.rollback_run("fixture_a", "Fixture rollback")
            assert (
                conn.execute(
                    "select run_id from enrichment.zoning_publication_pointer where city_code='fixture'"
                ).fetchone()[0]
                == "fixture_a"
            )
            assert (
                conn.execute(
                    "select count(*) from enrichment.zoning_publication_audit where city_code='fixture'"
                ).fetchone()[0]
                == 6
            )
            # Immutable results/snapshots/publications are guarded in PostgreSQL itself.
            for query in (
                "update intermediate.int_mlit__zoning_matches set far_pct=1 where run_id='fixture_a'",
                "update enrichment.zoning_run_inputs set latitude=1 where run_id='fixture_a'",
                "update enrichment.zoning_runs set input_fingerprint='changed' where run_id='fixture_a'",
            ):
                try:
                    with conn.transaction():
                        conn.execute(query)
                except Exception as exc:
                    assert "immutable" in str(exc).lower(), exc
                else:
                    raise AssertionError("Snapshot mutation was allowed")
            # Live output staleness uses current cache, not a materialized old input.
            live_run = conn.execute(
                "select run_id from enrichment.zoning_publication_pointer where city_code='27100'"
            ).fetchone()[0]
            live_building = conn.execute(
                "select building_key from intermediate.int_mlit__published_results where run_id=%s and zoning_status='matched' limit 1",
                (live_run,),
            ).fetchone()[0]
            with conn.transaction():
                conn.execute(
                    "update raw.suumo_building_locations set latitude=latitude+0.001 where building_key=%s and provider='google_maps_http' and query_version='building_name_chome_v1'",
                    (live_building,),
                )
                statuses = conn.execute(
                    "select distinct zoning_status,far_pct,bcr_pct,zoning_name from mart.rental_price_observations_with_zoning where building_key=%s",
                    (live_building,),
                ).fetchall()
                assert statuses == [("stale_location", None, None, None)], statuses
                prepared = p.prepare_run()
                assert prepared["run_id"] != live_run
                assert p.prepare_run()["run_id"] == prepared["run_id"]
                p.export_run(
                    live_run, "/opt/airflow/dbt/target/mlit_zoning/fixture_export"
                )
                exported = json.loads(
                    Path(
                        "/opt/airflow/dbt/target/mlit_zoning/fixture_export/manifest.json"
                    ).read_text()
                )
                assert exported["run"]["run_id"] == live_run
            # No publication still preserves the full observation grain.
            conn.execute(
                "delete from enrichment.zoning_publication_pointer where city_code='27100'"
            )
            assert (
                conn.execute(
                    "select count(*) from mart.rental_price_observations_with_zoning where zoning_status='no_publication'"
                ).fetchone()[0]
                == conn.execute(
                    "select count(*) from mart.fct_rental_price_observation"
                ).fetchone()[0]
            )
            conn.execute(
                "insert into enrichment.zoning_publication_pointer values ('27100',%s)",
                (live_run,),
            )
            # Spatial fixtures use the compiled production SQL, not a second matcher.
            query = Path(
                "/opt/airflow/dbt/target/compiled/japan_analysis/models/intermediate/int_mlit__zoning_matches.sql"
            ).read_text()
            query, replacements = re.subn(
                r"\br\.run_id\s*=\s*'[^']*'",
                "r.run_id = 'fixture_spatial'",
                query,
                count=1,
                flags=re.IGNORECASE,
            )
            assert replacements == 1, "Compiled SQL must contain the run filter"
            conn.execute(
                "insert into enrichment.zoning_runs(run_id,dataset_key,city_code,matching_version,input_fingerprint) values ('fixture_spatial','fixture_dataset','fixture','fixture','spatial')"
            )
            cx, cy = conn.execute(
                "select ST_X(p),ST_Y(p) from (select ST_Transform(ST_SetSRID(ST_MakePoint(135.5,34.7),4326),6674) p) x"
            ).fetchone()
            geom = (
                conn.execute(
                    "select ST_AsEWKB(ST_Transform(ST_MakeEnvelope(%s,%s,%s,%s,6674),6668))",
                    (cx, cy, cx + 100, cy + 100),
                )
                .fetchone()[0]
                .hex()
            )
            # Includes identical duplicated polygon (must deduplicate).
            for index in (1, 2):
                clone(
                    conn,
                    "intermediate.int_mlit__polygon_states",
                    {
                        "dataset_key": "fixture_dataset",
                        "feature_ordinal": index,
                        "zoning_area_key": "fixture_area",
                        "geom": geom,
                        "geometry_valid": True,
                        "attribute_quality": "valid",
                    },
                )
            for name, x, y, valid in [
                ("inside", 50, 50, True),
                ("below10", 9.9, 50, True),
                ("exact10", 10, 50, True),
                ("above10", 10.1, 50, True),
                ("on_boundary", 0, 50, True),
                ("outside", -10, 50, True),
                ("inverted", 50, 50, False),
            ]:
                lon, lat = conn.execute(
                    "select ST_X(p),ST_Y(p) from (select ST_Transform(ST_SetSRID(ST_MakePoint(%s,%s),6674),4326) p) t",
                    (cx + x, cy + y),
                ).fetchone()
                if not valid:
                    lat, lon = lon, lat
                fingerprint = "fixture_" + name
                conn.execute(
                    """insert into enrichment.zoning_run_inputs(run_id,building_key,latitude,longitude,
                location_status,coordinate_level,provider,location_fingerprint) values ('fixture_spatial',%s,%s,%s,'matched','building_poi','fixture',%s)""",
                    (name, lat, lon, fingerprint),
                )
            rows = conn.execute(query).fetchall()
            cols = [d.name for d in conn.execute(query).description]
            results = {
                dict(zip(cols, row))["building_key"]: dict(zip(cols, row))
                for row in rows
            }
            assert results["inside"]["zoning_status"] == "matched"
            assert results["inside"]["polygon_count"] == 1
            assert results["below10"]["zoning_status"] == "near_boundary"
            assert results["above10"]["zoning_status"] == "matched"
            assert results["outside"]["zoning_status"] == "not_found"
            assert results["inverted"]["zoning_status"] == "no_valid_location"
            assert results["on_boundary"]["zoning_status"] == "near_boundary", results[
                "on_boundary"
            ]
            assert results["exact10"]["zoning_status"] == "matched", results["exact10"]
            # Different polygon business state overlapping must produce ambiguity.
            clone(
                conn,
                "intermediate.int_mlit__polygon_states",
                {
                    "dataset_key": "fixture_dataset",
                    "feature_ordinal": 3,
                    "zoning_area_key": "fixture_area_overlap",
                    "geom": geom,
                    "geometry_valid": True,
                    "attribute_quality": "valid",
                    "far_pct": 600,
                },
            )
            overlap = {
                dict(zip(cols, row))["building_key"]: dict(zip(cols, row))
                for row in conn.execute(query)
            }
            assert overlap["inside"]["zoning_status"] == "ambiguous"
            # Invalid geometry blocks publication even explicit accepted-NULL decisions.
            fixture_dataset(conn, "fixture_invalid_dataset")
            clone(
                conn,
                "intermediate.int_mlit__polygon_states",
                {
                    "dataset_key": "fixture_invalid_dataset",
                    "feature_ordinal": 4,
                    "geometry_valid": False,
                },
            )
            fixture_run(conn, "fixture_geometry_error", "fixture_invalid_dataset")
            try:
                p.check_run("fixture_geometry_error")
            except RuntimeError as exc:
                assert "geometry" in str(exc)
            else:
                raise AssertionError("Invalid geometry passed")
            print(
                json.dumps(
                    {
                        "fixtures": "passed",
                        "history": "same dataset business version / A-B-A / failed run excluded",
                        "publication": "hold / accepted NULL with reason / rollback / immutable snapshots",
                        "spatial": "inside/outside/on-boundary/below-exact-above10/duplicates/overlap/inverted/CRS",
                        "exact_10m_distance": results["exact10"]["boundary_distance_m"],
                    }
                )
            )
    finally:
        conn.rollback()
        conn.close()


if __name__ == "__main__":
    main()
