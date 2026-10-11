"""Read-only acceptance: stored source hashes, spatial index and run reuse."""

import json
from pathlib import Path
from minio import Minio
from psycopg.rows import dict_row
from loaders.mlit_zoning_loader import digest
from loaders.mlit_zoning_publication import connection
from loaders.suumo_batch_loader import load_minio_config


def main():
    cfg = load_minio_config()
    client = Minio(
        cfg.endpoint,
        access_key=cfg.access_key,
        secret_key=cfg.secret_key,
        secure=cfg.secure,
    )
    objects = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("select * from raw.mlit_datasets order by dataset_key")
        datasets = list(cur.fetchall())
        assert datasets, "No loaded MLIT dataset"
        for d in datasets:
            for path, expected in [
                (d["zip_object_path"], d["zip_sha256"]),
                (d["metadata_object_path"], d["metadata_sha256"]),
                (d["manifest_object_path"], None),
            ]:
                response = client.get_object("mlit", path)
                try:
                    data = response.read()
                finally:
                    response.close()
                    response.release_conn()
                actual = digest(data)
                if expected:
                    assert actual == expected, (path, actual)
                else:
                    manifest = json.loads(data)
                    assert manifest["dataset_key"] == d["dataset_key"]
                    assert manifest["zip_sha256"] == d["zip_sha256"]
                    assert manifest["metadata_sha256"] == d["metadata_sha256"]
                    # Preserve the initial immutable bootstrap manifest too;
                    # later source-check manifests have a hash filename.
                    if Path(path).stem != "manifest":
                        assert actual == Path(path).stem
                objects.append(
                    {"object_path": path, "sha256": actual, "bytes": len(data)}
                )
        cur.execute(
            "select indexdef from pg_indexes where schemaname='intermediate' and tablename='int_mlit__polygon_states'"
        )
        indexes = [r["indexdef"] for r in cur.fetchall()]
        assert any("USING gist (geom)" in x for x in indexes), "Spatial index missing"
        cur.execute("select version() as postgres,postgis_full_version() as postgis")
        versions = cur.fetchone()
        cur.execute(
            "select count(*) as source_checks,count(*) filter(where reused) as reused_checks from raw.mlit_source_checks"
        )
        checks = cur.fetchone()
        assert checks["reused_checks"] > 0, "No observed idempotent source recheck"
        cur.execute("select distinct manifest_object_path from raw.mlit_source_checks")
        for row in cur.fetchall():
            path = row["manifest_object_path"]
            response = client.get_object("mlit", path)
            try:
                actual = digest(response.read())
            finally:
                response.close()
                response.release_conn()
            assert actual == Path(path).stem, (path, actual)
        cur.execute("select count(*) as datasets from raw.mlit_datasets")
        counts = cur.fetchone()
        cur.execute("select count(*) as polygons from raw.mlit_zoning_polygons")
        counts.update(cur.fetchone())
        cur.execute(
            "select building_key,count(*) as versions from mart.bridge_building_zoning group by building_key order by building_key"
        )
        history = list(cur.fetchall())
        result = {
            "source_objects": objects,
            "counts": counts,
            "source_checks": checks,
            "indexes": indexes,
            "runtime_versions": versions,
            "business_history": history,
        }
    Path("/opt/airflow/dbt/target/mlit_zoning/storage_verification.json").write_text(
        json.dumps(result, indent=2)
    )
    print(
        json.dumps(
            {"storage_hashes": "passed", "spatial_index": "present", **counts, **checks}
        )
    )


if __name__ == "__main__":
    main()
