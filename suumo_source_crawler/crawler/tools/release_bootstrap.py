from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence

import psycopg


CRAWLER_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_TABLES = (
    "config",
    "crawl_sources",
    "crawl_runs",
    "raw_snapshots",
    "crawl_tasks",
    "load_batches",
)


def parse_args() -> argparse.Namespace:
    """Parse release bootstrap options."""

    parser = argparse.ArgumentParser(
        description=(
            "Initialize the release runtime. By default this creates the DB schema "
            "only when it is missing, then runs main.py to create MinIO prefixes."
        )
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Do not check or create the PostgreSQL schema.",
    )
    parser.add_argument(
        "--skip-minio",
        action="store_true",
        help="Do not run main/main.py for MinIO bucket and prefix bootstrap.",
    )
    parser.add_argument(
        "--run-migrations",
        action="store_true",
        help="Run bundled SQL migrations after the schema check.",
    )
    parser.add_argument(
        "--force-db-reset",
        action="store_true",
        help=(
            "Run the full init SQL even when schema tables already exist. This is "
            "destructive because the init SQL drops crawler metadata tables first."
        ),
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=30,
        help="Number of connection attempts while waiting for services.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=2.0,
        help="Seconds to wait between connection attempts.",
    )
    return parser.parse_args()


def postgres_env() -> dict[str, str]:
    """Return PostgreSQL connection values from runtime environment variables."""

    return {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB", "suumo_crawler"),
        "user": os.getenv("POSTGRES_USER", "suumo_user"),
        "password": os.getenv("POSTGRES_PASSWORD", "suumo_password_change_me"),
    }


def connect_postgres():
    """Open an autocommit PostgreSQL connection for bootstrap checks."""

    config = postgres_env()
    return psycopg.connect(
        host=config["host"],
        port=int(config["port"]),
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        autocommit=True,
    )


def wait_for_postgres(attempts: int, sleep_seconds: float) -> None:
    """Wait until PostgreSQL accepts connections before running SQL files."""

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with connect_postgres() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            print("PostgreSQL is reachable")
            return
        except Exception as exc:  # noqa: BLE001 - bootstrap should report any connection failure.
            last_error = exc
            print(f"Waiting for PostgreSQL ({attempt}/{attempts}): {exc}")
            time.sleep(sleep_seconds)

    raise RuntimeError("PostgreSQL did not become reachable") from last_error


def bundled_file(relative_path: Sequence[str], env_name: str | None = None) -> Path:
    """Find a file bundled into the release image or present in a dev checkout."""

    candidates: list[Path] = []
    if env_name and os.getenv(env_name):
        candidates.append(Path(os.environ[env_name]))

    candidates.extend(
        [
            APP_ROOT.joinpath(*relative_path),
            APP_ROOT.parent.joinpath(*relative_path),
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Could not find {'/'.join(relative_path)}. Searched: {searched}")


def schema_state() -> tuple[set[str], set[str]]:
    """Return required metadata tables split into present and missing sets."""

    with connect_postgres() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s::text[])
                """,
                (list(REQUIRED_TABLES),),
            )
            present = {row[0] for row in cursor.fetchall()}

    required = set(REQUIRED_TABLES)
    return present, required - present


def run_psql_file(sql_path: Path) -> None:
    """Run one SQL file through psql so init files can keep psql directives."""

    config = postgres_env()
    env = os.environ.copy()
    env["PGPASSWORD"] = config["password"]
    command = [
        "psql",
        "-v",
        "ON_ERROR_STOP=1",
        "-h",
        config["host"],
        "-p",
        config["port"],
        "-U",
        config["user"],
        "-d",
        config["dbname"],
        "-f",
        str(sql_path),
    ]
    print(f"Running SQL file: {sql_path}")
    subprocess.run(command, check=True, env=env)


def ensure_database_schema(force_reset: bool, run_migrations: bool) -> None:
    """Create a fresh schema when absent, and optionally apply bundled migrations."""

    init_sql = bundled_file(
        ("docker", "postgres", "init", "001_create_crawler_metadata.sql"),
        env_name="CRAWLER_DB_SCHEMA_SQL",
    )
    present, missing = schema_state()

    if force_reset:
        print("Force reset requested. The full init SQL will drop and recreate crawler tables.")
        run_psql_file(init_sql)
    elif not present:
        print("No crawler metadata tables found. Creating fresh schema.")
        run_psql_file(init_sql)
    elif missing:
        missing_list = ", ".join(sorted(missing))
        present_list = ", ".join(sorted(present))
        raise RuntimeError(
            "Database has a partial crawler schema. "
            f"Present: {present_list}. Missing: {missing_list}. "
            "Run explicit migrations or use --force-db-reset only when deleting existing metadata is intended."
        )
    else:
        print("Crawler metadata schema already exists; skipping full init SQL.")

    if run_migrations:
        migrations_dir = bundled_file(
            ("docker", "postgres", "migrations"),
            env_name="CRAWLER_DB_MIGRATIONS_DIR",
        )
        for migration in sorted(migrations_dir.glob("*.sql")):
            run_psql_file(migration)


def run_minio_prefix_bootstrap(attempts: int, sleep_seconds: float) -> None:
    """Run main.py because that is the project-owned MinIO prefix initializer."""

    sys.path.insert(0, str(APP_ROOT))
    from main.main import main as minio_main  # pylint: disable=import-outside-toplevel

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            result = minio_main()
            if result != 0:
                raise RuntimeError(f"main.py returned non-zero status: {result}")
            print("MinIO buckets and prefixes are ready")
            return
        except Exception as exc:  # noqa: BLE001 - bootstrap should retry any MinIO startup error.
            last_error = exc
            print(f"Waiting for MinIO prefix bootstrap ({attempt}/{attempts}): {exc}")
            time.sleep(sleep_seconds)

    raise RuntimeError("MinIO prefix bootstrap did not complete") from last_error


def main() -> int:
    """Coordinate release bootstrap steps from one container command."""

    args = parse_args()

    if not args.skip_db:
        wait_for_postgres(args.attempts, args.sleep_seconds)
        ensure_database_schema(
            force_reset=args.force_db_reset,
            run_migrations=args.run_migrations,
        )

    if not args.skip_minio:
        run_minio_prefix_bootstrap(args.attempts, args.sleep_seconds)

    print("Crawler release bootstrap completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
