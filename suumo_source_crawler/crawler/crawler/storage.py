from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from typing import Mapping
from urllib.parse import urlparse, urlunparse

from minio import Minio


DEFAULT_BUCKET = "suumo"
PAGE_SOURCE_PREFIX = "page_source"
IMAGE_PREFIX = "image"
DATA_PREFIX = "data"
DEFAULT_COMPRESSION = "gzip"

CONTENT_TYPE_EXTENSIONS = {
    "application/json": ".json",
    "text/html": ".html",
}

SUUMO_DATA_HASH_FIELDS = (
    "image_public_url",
    "敷金",
    "管理費・共益費",
    "礼金",
    "保証金",
    "敷引・償却",
    "所在地",
    "駅徒歩",
    "間取り",
    "専有面積",
    "築年数",
    "階",
    "向き",
    "建物種別",
    "間取り詳細",
    "構造",
    "階建",
    "築年月",
    "エネルギー消費性能",
    "目安光熱費",
    "損保",
    "駐車場",
    "入居",
    "条件",
    "SUUMO物件コード",
    "情報更新日",
    "契約期間",
    "仲介手数料",
    "保証会社",
    "ほか初期費用",
    "ほか諸費用",
    "取引態様",
    "取り扱い店舗物件コード",
    "総戸数",
    "次回更新予定日",
)


@dataclass(frozen=True)
class StorageTarget:
    """Describe one MinIO object and the path saved into Postgres."""

    bucket_name: str
    object_name: str
    storage_path: str


@dataclass(frozen=True)
class StoredObject:
    """Return metadata needed by raw_snapshots, parser_records, or load_batches."""

    target: StorageTarget
    content_length: int
    content_hash: str
    compression: str | None
    stored_length: int


def sha256_bytes(payload: bytes) -> str:
    """Return a lowercase SHA-256 hex digest for bytes stored or compared later."""

    return sha256(payload).hexdigest()


def sha256_text(value: str) -> str:
    """Hash text as UTF-8 so URL hashes and data hashes are deterministic."""

    return sha256_bytes(value.encode("utf-8"))


def normalize_task_url(url: str, base_url: str = "https://suumo.jp") -> str:
    """Store SUUMO task URLs without the repeated scheme and host."""

    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)

    if parsed_url.scheme and parsed_url.netloc == parsed_base.netloc:
        return urlunparse(("", "", parsed_url.path, parsed_url.params, parsed_url.query, ""))

    return url


def task_url_hash(url: str, base_url: str = "https://suumo.jp") -> str:
    """Hash the normalized task URL used by crawl_tasks.url_hash."""

    return sha256_text(normalize_task_url(url, base_url=base_url))


def utc_path_datetime(value: datetime | None = None) -> str:
    """Format the datetime segment used in MinIO object paths."""

    if value is None:
        value = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def extension_for_content_type(content_type: str) -> str:
    """Map supported raw content types to object file extensions."""

    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    try:
        return CONTENT_TYPE_EXTENSIONS[media_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported content type: {content_type}") from exc


def build_storage_target(
    prefix: str,
    created_at: datetime,
    run_id: int,
    object_id: int,
    extension: str,
    bucket_name: str = DEFAULT_BUCKET,
    compression: str | None = DEFAULT_COMPRESSION,
) -> StorageTarget:
    """Build paths like suumo/page_source/{datetime}/{run_id}/{id}.html.gz."""

    normalized_extension = extension if extension.startswith(".") else f".{extension}"
    file_name = f"{object_id}{normalized_extension}"
    if compression == "gzip":
        file_name = f"{file_name}.gz"

    object_name = str(
        PurePosixPath(
            prefix.strip("/"),
            utc_path_datetime(created_at),
            str(run_id),
            file_name,
        )
    )
    return StorageTarget(
        bucket_name=bucket_name,
        object_name=object_name,
        storage_path=f"{bucket_name}/{object_name}",
    )


def compress_payload(payload: bytes, compression: str | None = DEFAULT_COMPRESSION) -> bytes:
    """Compress payload bytes before they are uploaded to MinIO."""

    if compression is None:
        return payload
    if compression == "gzip":
        return gzip.compress(payload)

    raise ValueError(f"Unsupported compression: {compression}")


def upload_bytes(
    client: Minio,
    target: StorageTarget,
    payload: bytes,
    content_type: str,
    compression: str | None = DEFAULT_COMPRESSION,
) -> StoredObject:
    """Upload bytes to MinIO and return DB-ready hash, length, and path metadata."""

    compressed_payload = compress_payload(payload, compression=compression)
    client.put_object(
        target.bucket_name,
        target.object_name,
        BytesIO(compressed_payload),
        length=len(compressed_payload),
        content_type=content_type,
    )
    return StoredObject(
        target=target,
        content_length=len(payload),
        content_hash=sha256_bytes(payload),
        compression=compression,
        stored_length=len(compressed_payload),
    )


def build_raw_snapshot_target(
    created_at: datetime,
    run_id: int,
    raw_snapshot_id: int,
    content_type: str,
    bucket_name: str = DEFAULT_BUCKET,
    compression: str | None = DEFAULT_COMPRESSION,
) -> StorageTarget:
    """Build the MinIO path for raw_snapshots.storage_path."""

    return build_storage_target(
        prefix=PAGE_SOURCE_PREFIX,
        created_at=created_at,
        run_id=run_id,
        object_id=raw_snapshot_id,
        extension=extension_for_content_type(content_type),
        bucket_name=bucket_name,
        compression=compression,
    )


def build_image_target(
    created_at: datetime,
    run_id: int,
    record_id: int,
    extension: str,
    bucket_name: str = DEFAULT_BUCKET,
    compression: str | None = None,
) -> StorageTarget:
    """Build the MinIO path for parser_records.image_storage_path."""

    return build_storage_target(
        prefix=IMAGE_PREFIX,
        created_at=created_at,
        run_id=run_id,
        object_id=record_id,
        extension=extension,
        bucket_name=bucket_name,
        compression=compression,
    )


def suumo_data_hash(record: Mapping[str, object | None]) -> str:
    """Hash only SUUMO source data fields, excluding generated DB/runtime state."""

    stable_payload = {
        field_name: record.get(field_name)
        for field_name in SUUMO_DATA_HASH_FIELDS
    }
    encoded_payload = json.dumps(
        stable_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(encoded_payload)
