from __future__ import annotations

import os
from dataclasses import dataclass
from io import BytesIO
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error


DEFAULT_BUCKET = "suumo"
DEFAULT_PREFIXES = ("data/", "page_source/", "image/")


@dataclass(frozen=True)
class MinioConfig:
    """Store MinIO connection settings and bucket/prefix bootstrap targets."""

    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    buckets: tuple[str, ...]
    main_bucket: str
    prefixes: tuple[str, ...]


def _csv_env(name: str, default: str) -> tuple[str, ...]:
    """Read a comma-separated environment variable and return non-empty values."""

    values = []
    for item in os.getenv(name, default).split(","):
        value = item.strip()
        if value:
            values.append(value)
    return tuple(values)


def _parse_endpoint(endpoint_url: str) -> tuple[str, bool]:
    """Convert a MinIO endpoint URL into the format required by the Minio client."""

    parsed = urlparse(endpoint_url)
    if parsed.scheme:
        return parsed.netloc, parsed.scheme == "https"
    return endpoint_url, False


def load_config() -> MinioConfig:
    """Load MinIO bootstrap configuration from environment variables."""

    endpoint_url = os.getenv("MINIO_ENDPOINT_URL")
    if not endpoint_url:
        # Local scripts may not receive MINIO_ENDPOINT_URL, so build it from host/port.
        host = os.getenv("MINIO_HOST", "localhost")
        port = os.getenv("MINIO_API_PORT", "9000")
        endpoint_url = f"http://{host}:{port}"

    endpoint, secure = _parse_endpoint(endpoint_url)
    buckets = _csv_env("MINIO_DEFAULT_BUCKETS", DEFAULT_BUCKET)
    main_bucket = os.getenv("MINIO_MAIN_BUCKET", buckets[0] if buckets else DEFAULT_BUCKET)
    prefixes = _csv_env("MINIO_MAIN_BUCKET_PREFIXES", ",".join(DEFAULT_PREFIXES))

    return MinioConfig(
        endpoint=endpoint,
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me"),
        secure=secure,
        buckets=buckets,
        main_bucket=main_bucket,
        # S3-style folders are prefixes, so keep a trailing slash for consistency.
        prefixes=tuple(prefix if prefix.endswith("/") else f"{prefix}/" for prefix in prefixes),
    )


def create_client(config: MinioConfig) -> Minio:
    """Create a MinIO client from the loaded runtime configuration."""

    return Minio(
        config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )


def ensure_bucket(client: Minio, bucket_name: str) -> None:
    """Create a bucket only when it does not already exist."""

    if client.bucket_exists(bucket_name):
        print(f"Bucket {bucket_name} already exists")
        return

    print(f"Creating bucket: {bucket_name}")
    client.make_bucket(bucket_name)


def object_exists(client: Minio, bucket_name: str, object_name: str) -> bool:
    """Check whether a specific object exists without modifying it."""

    try:
        client.stat_object(bucket_name, object_name)
        return True
    except S3Error as exc:
        if exc.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
            return False
        raise


def prefix_exists(client: Minio, bucket_name: str, prefix: str) -> bool:
    """Check whether a prefix exists either as a marker object or by containing data."""

    if object_exists(client, bucket_name, prefix):
        return True

    # A prefix can be real even when the zero-byte "folder marker" object is absent.
    for _ in client.list_objects(bucket_name, prefix=prefix, recursive=True):
        return True

    return False


def ensure_prefix(client: Minio, bucket_name: str, prefix: str) -> None:
    """Create a zero-byte prefix marker only when the path has no existing objects."""

    if prefix_exists(client, bucket_name, prefix):
        print(f"Path {bucket_name}/{prefix} already exists")
        return

    print(f"Creating path: {bucket_name}/{prefix}")
    # This creates a folder marker. It must not overwrite existing data under the prefix.
    client.put_object(bucket_name, prefix, BytesIO(b""), length=0)


def main() -> int:
    """Bootstrap required MinIO buckets and top-level prefixes for the crawler."""

    config = load_config()
    client = create_client(config)

    for bucket in config.buckets:
        ensure_bucket(client, bucket)

    if config.main_bucket not in config.buckets:
        ensure_bucket(client, config.main_bucket)

    for prefix in config.prefixes:
        ensure_prefix(client, config.main_bucket, prefix)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
