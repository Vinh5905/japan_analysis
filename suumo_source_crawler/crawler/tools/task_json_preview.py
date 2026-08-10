from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.metadata_db import connect_postgres
from crawler.object_storage import create_minio_client, split_storage_path


OUTPUT_DIR = Path("tmp/task_json_preview")


def parse_args() -> argparse.Namespace:
    """Parse task ids and output options for parser-record lookup."""

    parser = argparse.ArgumentParser(
        description=(
            "Find parser JSON records for one or more crawl_tasks.task_id values. "
            "The tool looks up each task's batch_id, downloads the batch JSON from "
            "MinIO, and returns matching parser records."
        ),
    )
    parser.add_argument(
        "task_ids",
        nargs="+",
        type=int,
        help="One or more crawl_tasks.task_id values.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory used when --write-json is set.",
    )
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write the result to disk instead of printing JSON to stdout.",
    )
    parser.add_argument(
        "--records-only",
        action="store_true",
        help="Return only matched parser record objects, without task/batch metadata.",
    )
    return parser.parse_args()


def unique_task_ids(task_ids: list[int]) -> list[int]:
    """Return task ids in input order without duplicates."""

    return list(dict.fromkeys(task_ids))


def fetch_task_batches(task_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Read task and batch metadata needed to locate parser JSON records."""

    query = """
        SELECT
            task.task_id,
            task.status::text,
            task.batch_id,
            batch.file_path,
            batch.file_format,
            batch.compression,
            batch.status::text AS batch_status,
            batch.created_at AS batch_created_at
        FROM crawl_tasks AS task
        LEFT JOIN load_batches AS batch
            ON task.batch_id = batch.batch_id
        WHERE task.task_id = ANY(%s)
        ORDER BY task.task_id
    """

    with connect_postgres() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (task_ids,))
            rows = cursor.fetchall()

    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        (
            task_id,
            task_status,
            batch_id,
            file_path,
            file_format,
            compression,
            batch_status,
            batch_created_at,
        ) = row
        result[int(task_id)] = {
            "task_id": int(task_id),
            "task_status": task_status,
            "batch_id": int(batch_id) if batch_id is not None else None,
            "file_path": file_path,
            "file_format": file_format,
            "compression": compression,
            "batch_status": batch_status,
            "batch_created_at": batch_created_at.isoformat()
            if batch_created_at is not None
            else None,
        }
    return result


def download_batch_records(file_path: str, compression: str | None) -> list[dict[str, Any]]:
    """Download and decode one load_batches JSON file from MinIO."""

    bucket_name, object_name = split_storage_path(file_path)
    minio_client = create_minio_client()
    response = minio_client.get_object(bucket_name, object_name)
    try:
        payload = response.read()
    finally:
        response.close()
        response.release_conn()

    if compression == "gzip" or object_name.endswith(".gz"):
        payload = gzip.decompress(payload)
    elif compression:
        raise ValueError(f"Unsupported batch compression: {compression}")

    records = json.loads(payload.decode("utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Batch payload must be a JSON array: {file_path}")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Batch payload contains a non-object record: {file_path}")
    return records


def records_by_task_id(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Index parser records by their task_id field."""

    indexed: dict[int, dict[str, Any]] = {}
    for record in records:
        task_id = record.get("task_id")
        if task_id is None:
            continue
        indexed[int(task_id)] = record
    return indexed


def fetch_parser_records(task_ids: list[int]) -> dict[str, Any]:
    """Build a JSON-serializable lookup result for requested task ids."""

    requested_task_ids = unique_task_ids(task_ids)
    task_metadata = fetch_task_batches(requested_task_ids)
    missing_task_ids = [
        task_id for task_id in requested_task_ids if task_id not in task_metadata
    ]
    tasks_without_batch = [
        task_id
        for task_id in requested_task_ids
        if task_id in task_metadata and task_metadata[task_id]["batch_id"] is None
    ]

    batch_groups: dict[str, list[int]] = defaultdict(list)
    for task_id in requested_task_ids:
        metadata = task_metadata.get(task_id)
        if not metadata or not metadata["file_path"]:
            continue
        batch_groups[metadata["file_path"]].append(task_id)

    matched_records: list[dict[str, Any]] = []
    unmatched_record_task_ids: list[int] = []
    for file_path, group_task_ids in batch_groups.items():
        metadata = task_metadata[group_task_ids[0]]
        batch_records = records_by_task_id(
            download_batch_records(
                file_path=file_path,
                compression=metadata["compression"],
            ),
        )
        for task_id in group_task_ids:
            record = batch_records.get(task_id)
            if record is None:
                unmatched_record_task_ids.append(task_id)
                continue
            matched_records.append(
                {
                    "task": task_metadata[task_id],
                    "record": record,
                },
            )

    return {
        "requested_task_ids": requested_task_ids,
        "matched_count": len(matched_records),
        "missing_task_ids": missing_task_ids,
        "tasks_without_batch": tasks_without_batch,
        "tasks_not_found_in_batch_json": unmatched_record_task_ids,
        "records": matched_records,
    }


def write_json_result(result: Any, output_dir: Path, task_ids: list[int]) -> Path:
    """Write lookup result to a deterministic local JSON file."""

    output_dir.mkdir(parents=True, exist_ok=True)
    task_id_part = "_".join(str(task_id) for task_id in unique_task_ids(task_ids))
    output_path = output_dir / f"task_records_{task_id_part}.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    """Fetch parser JSON records for requested crawl task ids."""

    args = parse_args()
    result = fetch_parser_records(args.task_ids)
    output_payload: Any
    if args.records_only:
        output_payload = [item["record"] for item in result["records"]]
    else:
        output_payload = result

    if args.write_json:
        output_path = write_json_result(
            result=output_payload,
            output_dir=Path(args.output_dir),
            task_ids=args.task_ids,
        )
        print(f"Wrote task parser records to {output_path}")
        return

    print(json.dumps(output_payload, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
