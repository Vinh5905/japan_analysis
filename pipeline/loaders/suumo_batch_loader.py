from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import psycopg
from minio import Minio
from psycopg.types.json import Jsonb


@dataclass(frozen=True)
class PostgresConfig:
    """Connection settings for one PostgreSQL database."""

    host: str
    port: int
    dbname: str
    user: str
    password: str


@dataclass(frozen=True)
class MinioConfig:
    """Connection settings for source MinIO."""

    endpoint: str
    access_key: str
    secret_key: str
    secure: bool


@dataclass(frozen=True)
class SourceBatch:
    """Source load_batches row claimed for loading."""

    batch_id: int
    source_id: int
    file_path: str
    file_format: str
    compression: str | None
    row_count: int


def load_source_postgres_config() -> PostgresConfig:
    """Load source crawler metadata database settings from environment."""

    return PostgresConfig(
        host=os.getenv("SOURCE_POSTGRES_HOST", "postgres"),
        port=int(os.getenv("SOURCE_POSTGRES_PORT", "5432")),
        dbname=os.getenv("SOURCE_POSTGRES_DB", "suumo_crawler"),
        user=os.getenv("SOURCE_POSTGRES_USER", "suumo_user"),
        password=os.getenv("SOURCE_POSTGRES_PASSWORD", "suumo_password_change_me"),
    )


def load_warehouse_postgres_config() -> PostgresConfig:
    """Load warehouse database settings from environment."""

    return PostgresConfig(
        host=os.getenv("WAREHOUSE_POSTGRES_HOST", "warehouse-postgres"),
        port=int(os.getenv("WAREHOUSE_POSTGRES_PORT", "5432")),
        dbname=os.getenv("WAREHOUSE_DB", "japan_warehouse"),
        user=os.getenv("PIPELINE_POSTGRES_USER", "pipeline_admin"),
        password=os.getenv("PIPELINE_POSTGRES_PASSWORD", "pipeline_password_change_me"),
    )


def load_minio_config() -> MinioConfig:
    """Load source MinIO settings from environment."""

    endpoint_url = os.getenv("SOURCE_MINIO_ENDPOINT_URL", "http://minio:9000")
    parsed_url = urlparse(endpoint_url)
    if parsed_url.scheme:
        endpoint = parsed_url.netloc
        secure = parsed_url.scheme == "https"
    else:
        endpoint = endpoint_url
        secure = False

    return MinioConfig(
        endpoint=endpoint,
        access_key=os.getenv("SOURCE_MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("SOURCE_MINIO_ROOT_PASSWORD", "minioadmin_change_me"),
        secure=secure,
    )


def postgres_connection(config: PostgresConfig):
    """Create a psycopg connection from a PostgresConfig."""

    return psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
    )


def list_pending_batch_ids(limit: int) -> list[int]:
    """Return pending source batch ids in creation order."""

    source_config = load_source_postgres_config()
    with postgres_connection(source_config) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT batch_id
                FROM load_batches
                WHERE status = 'pending'
                ORDER BY created_at, batch_id
                LIMIT %s
                """,
                (limit,),
            )
            return [int(row[0]) for row in cursor.fetchall()]


def claim_source_batch(batch_id: int) -> SourceBatch | None:
    """Move a pending source batch to loading and return its metadata."""

    source_config = load_source_postgres_config()
    with postgres_connection(source_config) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE load_batches
                    SET
                        status = 'loading',
                        started_loading_at = now(),
                        finished_loading_at = NULL,
                        loaded_at = NULL,
                        error_message = NULL
                    WHERE batch_id = %s
                      AND status = 'pending'
                    RETURNING
                        batch_id,
                        source_id,
                        file_path,
                        file_format,
                        compression,
                        row_count
                    """,
                    (batch_id,),
                )
                row = cursor.fetchone()
                if row is None:
                    return None

                return SourceBatch(
                    batch_id=int(row[0]),
                    source_id=int(row[1]),
                    file_path=row[2],
                    file_format=row[3],
                    compression=row[4],
                    row_count=int(row[5]),
                )


def mark_source_batch_success(
    batch_id: int,
    inserted_count: int,
    failed_count: int,
) -> None:
    """Mark a source batch loaded after warehouse writes finish."""

    source_config = load_source_postgres_config()
    with postgres_connection(source_config) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE load_batches
                    SET
                        status = 'success',
                        inserted_count = %s,
                        failed_count = %s,
                        error_message = NULL,
                        finished_loading_at = now(),
                        loaded_at = now()
                    WHERE batch_id = %s
                    """,
                    (
                        inserted_count,
                        failed_count,
                        batch_id,
                    ),
                )


def mark_source_batch_failed(batch_id: int, error_message: str) -> None:
    """Mark a source batch failed when the whole file cannot be loaded."""

    source_config = load_source_postgres_config()
    with postgres_connection(source_config) as connection:
        with connection.transaction():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE load_batches
                    SET
                        status = 'failed',
                        error_message = %s,
                        finished_loading_at = now(),
                        loaded_at = NULL
                    WHERE batch_id = %s
                    """,
                    (error_message[:4000], batch_id),
                )


def split_storage_path(storage_path: str) -> tuple[str, str]:
    """Split a logical MinIO path like suumo/data/file.json.gz."""

    bucket_name, separator, object_name = storage_path.strip("/").partition("/")
    if not bucket_name or not separator or not object_name:
        raise ValueError(f"Invalid MinIO storage path: {storage_path}")

    return bucket_name, object_name


def read_minio_batch(batch: SourceBatch) -> list[Any]:
    """Download and decode one parser-record JSON batch from MinIO."""

    if batch.file_format != "json":
        raise ValueError(f"Unsupported batch file_format={batch.file_format!r}")

    bucket_name, object_name = split_storage_path(batch.file_path)
    minio_config = load_minio_config()
    client = Minio(
        minio_config.endpoint,
        access_key=minio_config.access_key,
        secret_key=minio_config.secret_key,
        secure=minio_config.secure,
    )

    response = client.get_object(bucket_name, object_name)
    try:
        payload = response.read()
    finally:
        response.close()
        response.release_conn()

    if batch.compression == "gzip":
        payload = gzip.decompress(payload)
    elif batch.compression:
        raise ValueError(f"Unsupported batch compression={batch.compression!r}")

    records = json.loads(payload.decode("utf-8"))
    if not isinstance(records, list):
        raise ValueError("Batch JSON payload must be an array")

    return records


def load_records_to_warehouse(batch: SourceBatch, records: list[Any]) -> dict[str, int]:
    """Write only valid parser records into raw.suumo_parser_records."""

    warehouse_config = load_warehouse_postgres_config()
    inserted_count = 0
    failed_count = 0
    loaded_at = datetime.now(timezone.utc)

    with postgres_connection(warehouse_config) as connection:
        for record in records:
            try:
                if not isinstance(record, dict):
                    raise ValueError("Parser record must be a JSON object")
                if record.get("is_valid") is not True:
                    failed_count += 1
                    continue

                task_id = int(record["task_id"])
                data_hash = str(record["data_hash"])
                if not data_hash:
                    raise ValueError("Parser record data_hash is empty")

                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO raw.suumo_parser_records (
                                task_id,
                                batch_id,
                                source_id,
                                data_hash,
                                record,
                                loaded_at,
                                created_at,
                                updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, now(), now())
                            ON CONFLICT (task_id)
                            DO UPDATE SET
                                batch_id = EXCLUDED.batch_id,
                                source_id = EXCLUDED.source_id,
                                data_hash = EXCLUDED.data_hash,
                                record = EXCLUDED.record,
                                loaded_at = EXCLUDED.loaded_at,
                                updated_at = now()
                            """,
                            (
                                task_id,
                                batch.batch_id,
                                batch.source_id,
                                data_hash,
                                Jsonb(record),
                                loaded_at,
                            ),
                        )
                inserted_count += 1
            except Exception:
                failed_count += 1

    return {
        "inserted_count": inserted_count,
        "failed_count": failed_count,
    }


def load_one_batch(batch_id: int) -> dict[str, Any]:
    """Claim and load one source batch if it is still pending."""

    batch = claim_source_batch(batch_id)
    if batch is None:
        return {
            "batch_id": batch_id,
            "status": "skipped",
            "reason": "batch is not pending",
        }

    try:
        records = read_minio_batch(batch)
        counts = load_records_to_warehouse(batch, records)
        mark_source_batch_success(batch.batch_id, **counts)
        return {
            "batch_id": batch.batch_id,
            "status": "success",
            "file_path": batch.file_path,
            "row_count": len(records),
            **counts,
        }
    except Exception as exc:
        mark_source_batch_failed(batch.batch_id, str(exc))
        return {
            "batch_id": batch.batch_id,
            "status": "failed",
            "file_path": batch.file_path,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }


def load_pending_batches(
    batch_ids: list[int] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Load explicit batch ids or poll source DB for pending batches."""

    if batch_ids is None:
        effective_limit = limit or int(os.getenv("SUUMO_LOAD_BATCH_LIMIT", "20"))
        batch_ids = list_pending_batch_ids(effective_limit)

    results = [load_one_batch(int(batch_id)) for batch_id in batch_ids]
    loaded_batch_ids = [
        int(result["batch_id"])
        for result in results
        if result.get("status") == "success"
    ]
    return {
        "requested_batch_ids": batch_ids,
        "loaded_batch_ids": loaded_batch_ids,
        "loaded_count": len(loaded_batch_ids),
        "results": results,
    }
