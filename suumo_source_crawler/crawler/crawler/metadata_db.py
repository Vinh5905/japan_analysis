from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import psycopg
from psycopg import Connection
from psycopg.rows import tuple_row


@dataclass(frozen=True)
class PostgresConfig:
    """Store PostgreSQL connection settings from the crawler environment."""

    host: str
    port: int
    dbname: str
    user: str
    password: str


@dataclass(frozen=True)
class CrawlRunRecord:
    """Represent the crawl_runs row created for one spider execution."""

    run_id: int
    created_at: datetime


@dataclass(frozen=True)
class RawSnapshotRecord:
    """Store DB metadata for one fetched raw payload."""

    raw_snapshot_id: int
    url: str
    final_url: str | None
    http_status: int
    content_type: str
    content_length: int
    content_hash: str
    storage_path: str
    compression: str | None
    encoding: str | None


@dataclass(frozen=True)
class PendingParseTask:
    """Represent one pending crawl task with its stored raw snapshot."""

    task_id: int
    run_id: int
    source_id: int
    task_url: str
    raw_snapshot_id: int
    storage_path: str


def load_postgres_config() -> PostgresConfig:
    """Load PostgreSQL connection settings from environment variables."""

    return PostgresConfig(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.getenv("POSTGRES_DB", "japan_analysis"),
        user=os.getenv("POSTGRES_USER", "japan_analysis_user"),
        password=os.getenv("POSTGRES_PASSWORD", "japan_analysis_password_change_me"),
    )


def connect_postgres(config: PostgresConfig | None = None) -> Connection:
    """Open an autocommit psycopg connection for spider metadata writes."""

    if config is None:
        config = load_postgres_config()

    return psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
        autocommit=True,
        row_factory=tuple_row,
    )


class CrawlerMetadataRepository:
    """Provide focused SQL operations for crawler metadata tables."""

    def __init__(self, connection: Connection):
        """Store the open PostgreSQL connection used by this repository."""

        self.connection = connection

    @classmethod
    def from_env(cls) -> "CrawlerMetadataRepository":
        """Create a repository using environment-backed PostgreSQL settings."""

        return cls(connect_postgres())

    def close(self) -> None:
        """Close the underlying PostgreSQL connection."""

        self.connection.close()

    def fetch_existing_task_hashes(self, url_hashes: Iterable[str]) -> set[str]:
        """Return url_hash values that already exist in crawl_tasks."""

        unique_hashes = list(dict.fromkeys(url_hashes))
        if not unique_hashes:
            return set()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT url_hash
                FROM crawl_tasks
                WHERE url_hash = ANY(%s::text[])
                """,
                (unique_hashes,),
            )
            return {row[0] for row in cursor.fetchall()}

    def create_crawl_run(
        self,
        source_id: int = 1,
        created_by: str = "schedule",
    ) -> CrawlRunRecord:
        """Insert one crawl_runs row for a spider execution."""

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO crawl_runs (source_id, created_by)
                VALUES (%s, %s)
                RETURNING run_id, created_at
                """,
                (source_id, created_by),
            )
            run_id, created_at = cursor.fetchone()
            return CrawlRunRecord(run_id=int(run_id), created_at=created_at)

    def finish_crawl_run(self, run_id: int) -> None:
        """Mark a crawl run as finished when the spider closes."""

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE crawl_runs
                SET finished_at = now()
                WHERE run_id = %s
                """,
                (run_id,),
            )

    def finalize_unfinished_run_tasks(
        self,
        run_id: int,
        error_type: str,
        error_message: str,
    ) -> int:
        """Mark claimed but unfinished tasks as failed when the spider closes."""

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                WITH unfinished_tasks AS (
                    UPDATE crawl_tasks
                    SET
                        status = 'failed',
                        error_type = %s,
                        error_message = %s,
                        fetched_at = NULL,
                        raw_snapshot_id = NULL
                    WHERE run_id = %s
                      AND status = 'failed'
                      AND error_type IS NULL
                      AND fetched_at IS NULL
                      AND raw_snapshot_id IS NULL
                    RETURNING task_id
                ),
                unfinished_count AS (
                    SELECT count(*)::integer AS total
                    FROM unfinished_tasks
                )
                UPDATE crawl_runs
                SET total_urls = total_urls + unfinished_count.total
                FROM unfinished_count
                WHERE crawl_runs.run_id = %s
                RETURNING unfinished_count.total
                """,
                (
                    error_type,
                    error_message[:4000],
                    run_id,
                    run_id,
                ),
            )
            result = cursor.fetchone()
            return int(result[0]) if result is not None else 0

    def create_run_task(
        self,
        run_id: int,
        task_url: str,
        url_hash: str,
        method: str,
        scheduled_at: datetime,
    ) -> int | None:
        """Create the one crawl_tasks row when a request starts downloading."""

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO crawl_tasks (
                        run_id,
                        url,
                        url_hash,
                        method,
                        status,
                        scheduled_at
                    )
                    VALUES (%s, %s, %s, %s, 'failed', %s)
                    ON CONFLICT (run_id, url_hash) DO NOTHING
                    RETURNING task_id
                    """,
                    (
                        run_id,
                        task_url,
                        url_hash,
                        method,
                        scheduled_at,
                    ),
                )
                inserted_task = cursor.fetchone()
                if inserted_task is None:
                    return None

                return int(inserted_task[0])

    def fetch_pending_parse_tasks(self, limit: int = 0) -> list[PendingParseTask]:
        """Return crawl tasks whose raw snapshots are ready for parser batching."""

        limit_clause = ""
        params: list[object] = []
        if limit > 0:
            limit_clause = "LIMIT %s"
            params.append(limit)

        with self.connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    ct.task_id,
                    ct.run_id,
                    cr.source_id,
                    ct.url,
                    ct.raw_snapshot_id,
                    rs.storage_path
                FROM crawl_tasks AS ct
                JOIN crawl_runs AS cr
                    ON cr.run_id = ct.run_id
                JOIN raw_snapshots AS rs
                    ON rs.raw_snapshot_id = ct.raw_snapshot_id
                WHERE ct.status = 'pending'
                  AND ct.raw_snapshot_id IS NOT NULL
                  AND ct.batch_id IS NULL
                ORDER BY ct.task_id
                {limit_clause}
                """,
                params,
            )
            return [
                PendingParseTask(
                    task_id=int(row[0]),
                    run_id=int(row[1]),
                    source_id=int(row[2]),
                    task_url=row[3],
                    raw_snapshot_id=int(row[4]),
                    storage_path=row[5],
                )
                for row in cursor.fetchall()
            ]

    def reserve_load_batch_id(self) -> int:
        """Reserve a load_batches.batch_id before building the MinIO path."""

        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(pg_get_serial_sequence('load_batches', 'batch_id'))"
            )
            return int(cursor.fetchone()[0])

    def create_load_batch_and_attach_tasks(
        self,
        batch_id: int,
        source_id: int,
        file_path: str,
        file_format: str,
        compression: str | None,
        row_count: int,
        file_hash: str,
        task_ids: list[int],
    ) -> None:
        """Insert load_batches metadata and connect parsed tasks to that batch."""

        if not task_ids:
            raise ValueError("Cannot create a load batch without task ids")

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO load_batches (
                        batch_id,
                        source_id,
                        file_path,
                        file_format,
                        compression,
                        row_count,
                        file_hash,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
                    """,
                    (
                        batch_id,
                        source_id,
                        file_path,
                        file_format,
                        compression,
                        row_count,
                        file_hash,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE crawl_tasks
                    SET
                        batch_id = %s,
                        status = 'success',
                        error_type = NULL,
                        error_message = NULL
                    WHERE task_id = ANY(%s::bigint[])
                    """,
                    (
                        batch_id,
                        task_ids,
                    ),
                )

    def reserve_raw_snapshot_id(self) -> int:
        """Reserve a raw_snapshot_id before building the matching MinIO path."""

        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT nextval(pg_get_serial_sequence('raw_snapshots', 'raw_snapshot_id'))"
            )
            return int(cursor.fetchone()[0])

    def mark_task_pending_with_snapshot(
        self,
        task_id: int,
        fetched_at: datetime,
        snapshot: RawSnapshotRecord,
    ) -> None:
        """Insert raw_snapshots and update the existing task to pending."""

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                should_increment_total_urls = self.should_increment_total_urls(
                    cursor,
                    task_id,
                )
                cursor.execute(
                    """
                    INSERT INTO raw_snapshots (
                        raw_snapshot_id,
                        url,
                        final_url,
                        http_status,
                        content_type,
                        content_length,
                        content_hash,
                        storage_path,
                        compression,
                        encoding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        snapshot.raw_snapshot_id,
                        snapshot.url,
                        snapshot.final_url,
                        snapshot.http_status,
                        snapshot.content_type,
                        snapshot.content_length,
                        snapshot.content_hash,
                        snapshot.storage_path,
                        snapshot.compression,
                        snapshot.encoding,
                    ),
                )
                cursor.execute(
                    """
                    UPDATE crawl_tasks
                    SET
                        status = 'pending',
                        error_type = NULL,
                        error_message = NULL,
                        fetched_at = %s,
                        raw_snapshot_id = %s
                    WHERE task_id = %s
                    """,
                    (
                        fetched_at,
                        snapshot.raw_snapshot_id,
                        task_id,
                    ),
                )
                if should_increment_total_urls:
                    self.increment_run_total_urls(cursor, task_id)

    def mark_task_failed(
        self,
        task_id: int,
        error_type: str,
        error_message: str,
    ) -> None:
        """Update the current run's task row after retries are exhausted."""

        with self.connection.transaction():
            with self.connection.cursor() as cursor:
                should_increment_total_urls = self.should_increment_total_urls(
                    cursor,
                    task_id,
                )
                cursor.execute(
                    """
                    UPDATE crawl_tasks
                    SET
                        status = 'failed',
                        error_type = %s,
                        error_message = %s,
                        fetched_at = NULL,
                        raw_snapshot_id = NULL
                    WHERE task_id = %s
                    """,
                    (
                        error_type,
                        error_message[:4000],
                        task_id,
                    ),
                )
                if should_increment_total_urls:
                    self.increment_run_total_urls(cursor, task_id)

    def should_increment_total_urls(self, cursor, task_id: int) -> bool:
        """Return true when this task has not yet been counted in crawl_runs."""

        cursor.execute(
            """
            SELECT error_type, fetched_at, raw_snapshot_id
            FROM crawl_tasks
            WHERE task_id = %s
            FOR UPDATE
            """,
            (task_id,),
        )
        task_state = cursor.fetchone()
        if task_state is None:
            raise ValueError(f"crawl_tasks row does not exist: task_id={task_id}")

        error_type, fetched_at, raw_snapshot_id = task_state
        return error_type is None and fetched_at is None and raw_snapshot_id is None

    def increment_run_total_urls(self, cursor, task_id: int) -> None:
        """Increment crawl_runs.total_urls for the task's run."""

        cursor.execute(
            """
            UPDATE crawl_runs
            SET total_urls = total_urls + 1
            WHERE run_id = (
                SELECT run_id
                FROM crawl_tasks
                WHERE task_id = %s
            )
            """,
            (task_id,),
        )
