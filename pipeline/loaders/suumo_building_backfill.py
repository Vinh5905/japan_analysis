"""Backfill building headlines from existing local snapshots; never rerun crawling."""

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import HTTPError
from psycopg.rows import dict_row
from crawler.building_identity import (
    BUILDING_RECORD_FIELDS,
    PARSER_VERSION,
    extract_building_identity,
    extract_property_code,
)
from loaders.suumo_batch_loader import (
    load_minio_config,
    load_source_postgres_config,
    load_warehouse_postgres_config,
    postgres_connection,
    split_storage_path,
)


def ensure_table():
    """Apply the shared idempotent DDL without resetting any warehouse data."""
    ddl = (
        Path(__file__).resolve().parents[1]
        / "warehouse/suumo_building_name_backfill.sql"
    )
    with postgres_connection(load_warehouse_postgres_config()) as connection:
        connection.execute(ddl.read_text())


def read_snapshot(client, row):
    """Validate original uncompressed bytes before decoding stored HTML."""
    bucket, key = split_storage_path(row["storage_path"])
    response = client.get_object(bucket, key)
    try:
        payload = response.read()
    finally:
        response.close()
        response.release_conn()
    if row["compression"] == "gzip":
        payload = gzip.decompress(payload)
    elif row["compression"]:
        raise ValueError("Unsupported snapshot compression")
    if hashlib.sha256(payload).hexdigest() != row["content_hash"]:
        raise ValueError("Snapshot content hash mismatch")
    return payload.decode(row["encoding"] or "utf-8")


def persist_result(connection, result):
    """Upsert audit metadata; a failed refresh cannot erase a parsed name."""
    columns = (
        "source_id",
        "task_id",
        "suumo_property_code",
        "raw_snapshot_id",
        "storage_path",
        "content_hash",
        "parser_version",
        *BUILDING_RECORD_FIELDS,
        "error_message",
    )
    updates = ", ".join(f"{name} = excluded.{name}" for name in columns[2:])
    connection.execute(
        f"""
        insert into raw.suumo_building_name_backfill ({", ".join(columns)})
        values ({", ".join(["%s"] * len(columns))})
        on conflict (source_id, task_id) do update set {updates}, backfilled_at = now()
        where excluded.building_name_parse_status = 'parsed'
           or suumo_building_name_backfill.building_name_parse_status <> 'parsed'
    """,
        [result.get(name) for name in columns],
    )


def backfill(limit=None, dry_run=False, force=False, report=None):
    """Read snapshots and write only the enrichment table, committing per task."""
    if not dry_run:
        ensure_table()
    with postgres_connection(load_source_postgres_config()) as source:
        rows = (
            source.cursor(row_factory=dict_row)
            .execute("""
            select t.task_id, r.source_id, s.raw_snapshot_id, s.storage_path,
                   s.content_hash, s.compression, s.encoding
            from crawl_tasks t join crawl_runs r using (run_id)
            join raw_snapshots s using (raw_snapshot_id)
            where s.content_type = 'text/html' and s.http_status = 200
            order by t.task_id
        """)
            .fetchall()
        )
    config = load_minio_config()
    client = Minio(
        config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )
    summary = {
        "available": len(rows),
        "processed": 0,
        "cache_hit": 0,
        "parsed": 0,
        "unmatched": 0,
        "errors": 0,
        "dry_run": dry_run,
    }
    results = []
    with postgres_connection(load_warehouse_postgres_config()) as warehouse:
        exists = warehouse.execute(
            "select to_regclass('raw.suumo_building_name_backfill')"
        ).fetchone()[0]
        cache = (
            {}
            if not exists
            else {
                (r["source_id"], r["task_id"]): r
                for r in warehouse.cursor(row_factory=dict_row)
                .execute("select * from raw.suumo_building_name_backfill")
                .fetchall()
            }
        )
        for row in rows:
            previous = cache.get((row["source_id"], row["task_id"]))
            if (
                not force
                and previous
                and previous["content_hash"] == row["content_hash"]
                and previous["parser_version"] == PARSER_VERSION
            ):
                summary["cache_hit"] += 1
                continue
            if limit is not None and summary["processed"] >= limit:
                break
            result = {**row, "parser_version": PARSER_VERSION, "error_message": None}
            try:
                html = read_snapshot(client, row)
            except (S3Error, HTTPError, OSError, UnicodeError, ValueError) as error:
                result.update({name: None for name in BUILDING_RECORD_FIELDS})
                result.update(
                    building_name_parse_status="snapshot_error",
                    error_message=f"{type(error).__name__}: {error}"[:1000],
                )
                summary["errors"] += 1
            else:
                # Parser/code errors propagate: only external snapshot failures are recoverable.
                result.update(extract_building_identity(html))
                result["suumo_property_code"] = extract_property_code(html)
                if not result["suumo_property_code"]:
                    result.update(
                        building_name_raw=None,
                        room_number_raw=None,
                        building_name_parse_status="missing_property_code",
                    )
                summary[
                    "parsed"
                    if result["building_name_parse_status"] == "parsed"
                    else "unmatched"
                ] += 1
            # Warehouse errors must fail the task rather than being swallowed as HTML errors.
            if not dry_run:
                persist_result(warehouse, result)
                warehouse.commit()
            results.append(
                {
                    name: result.get(name)
                    for name in (
                        "source_id",
                        "task_id",
                        "raw_snapshot_id",
                        "storage_path",
                        "suumo_property_code",
                        *BUILDING_RECORD_FIELDS,
                        "error_message",
                    )
                }
            )
            summary["processed"] += 1
    if report:
        destination = Path(report)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if results:
            with destination.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(results[0]))
                writer.writeheader()
                writer.writerows(results)
    return summary


def main():
    """Expose bounded local backfill and initialization commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--init-only", action="store_true")
    parser.add_argument("--report", help="Local CSV comparison report")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.dry_run and args.init_only:
        parser.error("--dry-run and --init-only are mutually exclusive")
    if args.init_only:
        ensure_table()
        print(json.dumps({"initialized": True}))
    else:
        print(json.dumps(backfill(args.limit, args.dry_run, args.force, args.report)))


if __name__ == "__main__":
    main()
