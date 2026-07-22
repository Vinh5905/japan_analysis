from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from minio import Minio


@dataclass(frozen=True)
class MinioConfig:
    """Store MinIO connection settings used by Scrapy spiders."""

    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    bucket_name: str


def parse_endpoint(endpoint_url: str) -> tuple[str, bool]:
    """Convert an HTTP endpoint URL into Minio client endpoint arguments."""

    parsed_url = urlparse(endpoint_url)
    if parsed_url.scheme:
        return parsed_url.netloc, parsed_url.scheme == "https"

    return endpoint_url, False


def load_minio_config() -> MinioConfig:
    """Load MinIO config from the crawler container environment."""

    endpoint_url = os.getenv("MINIO_ENDPOINT_URL", "http://minio:9000")
    endpoint, secure = parse_endpoint(endpoint_url)

    return MinioConfig(
        endpoint=endpoint,
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin_change_me"),
        secure=secure,
        bucket_name=os.getenv("MINIO_MAIN_BUCKET", "suumo"),
    )


def create_minio_client(config: MinioConfig | None = None) -> Minio:
    """Create a MinIO client from environment-backed config."""

    if config is None:
        config = load_minio_config()

    return Minio(
        config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )


def split_storage_path(storage_path: str) -> tuple[str, str]:
    """Split a logical storage path like suumo/page_source/... into bucket/key."""

    bucket_name, separator, object_name = storage_path.strip("/").partition("/")
    if not bucket_name or not separator or not object_name:
        raise ValueError(f"Invalid MinIO storage path: {storage_path}")

    return bucket_name, object_name
