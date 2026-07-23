from __future__ import annotations

import gzip
import json
from datetime import datetime, timedelta, timezone

import scrapy
from scrapy import signals
from scrapy.http import TextResponse

from crawler.metadata_db import CrawlerMetadataRepository, PendingParseTask
from crawler.object_storage import create_minio_client, load_minio_config, split_storage_path
from crawler.storage import (
    SUUMO_DATA_HASH_FIELDS,
    build_batch_target,
    suumo_data_hash,
    upload_bytes,
)


SUUMO_SOURCE_FIELD_NAMES = tuple(
    field_name
    for field_name in SUUMO_DATA_HASH_FIELDS
    if field_name != "image_public_url"
)
PARSER_RECORD_FIELD_NAMES = (
    "task_id",
    "image_public_url",
    "image_storage_path",
    *SUUMO_SOURCE_FIELD_NAMES,
    "data_hash",
    "parsed_at",
    "is_valid",
    "error_type",
    "error_message",
)


def safe_extract(selector) -> str:
    """Extract normalized visible text from a Scrapy selector or selector list."""

    text = selector.xpath("string()").get()
    return text.strip().replace("\t", "") if text else ""


def null_if_empty(value: object | None) -> object | None:
    """Convert empty strings to JSON null while preserving non-string values."""

    if value is None:
        return None
    if isinstance(value, str):
        normalized_value = value.strip()
        return normalized_value or None

    return value


class SuumoPageSpider(scrapy.Spider):
    """Parse pending SUUMO raw snapshots into compressed JSON load batches."""

    name = "suumo_page"
    allowed_domains = ["suumo.jp"]

    def __init__(self, *args, **kwargs):
        """Initialize settings-backed parser batch state."""

        super().__init__(*args, **kwargs)
        self.task_limit = 0
        self.batch_size = 100
        self.batch_seconds = 300
        self.source_id = 1
        self.source_base_url = "https://suumo.jp"
        self.batch_records: list[dict[str, object | None]] = []
        self.batch_started_at: datetime | None = None
        self.metadata_repository: CrawlerMetadataRepository | None = None
        self.minio_config = load_minio_config()
        self.minio_client = create_minio_client(self.minio_config)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Create the spider and load parser batch settings."""

        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.task_limit = crawler.settings.getint("SUUMO_PAGE_TASK_LIMIT", 0)
        spider.batch_size = crawler.settings.getint("SUUMO_PAGE_BATCH_SIZE", 100)
        spider.batch_seconds = crawler.settings.getint("SUUMO_PAGE_BATCH_SECONDS", 300)
        spider.source_id = crawler.settings.getint("SUUMO_SOURCE_ID", 1)
        spider.source_base_url = crawler.settings.get("SUUMO_SOURCE_BASE_URL", "https://suumo.jp")
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)
        return spider

    def open_spider(self, spider):
        """Open DB resources used by parser batch persistence."""

        self.metadata_repository = CrawlerMetadataRepository.from_env()
        self.ensure_bucket()

    def close_spider(self, spider, reason):
        """Flush any buffered records before closing DB resources."""

        try:
            if self.batch_records:
                self.logger.info(
                    "Flushing %s buffered parser records before close: %s",
                    len(self.batch_records),
                    reason,
                )
                self.flush_batch(reason=f"spider_closed:{reason}")
        except Exception:
            self.logger.exception("Failed to flush buffered parser records on close")
        finally:
            if self.metadata_repository is not None:
                self.metadata_repository.close()
                self.metadata_repository = None

    async def start(self):
        """Read pending crawl tasks from DB and persist parser records in batches."""

        metadata_repository = self.require_metadata_repository()
        pending_tasks = metadata_repository.fetch_pending_parse_tasks(
            limit=self.task_limit,
        )
        if not pending_tasks:
            self.logger.warning("No pending SUUMO crawl_tasks found for parser batching")
            return

        self.logger.info(
            "Starting SUUMO parser batching for %s pending tasks",
            len(pending_tasks),
        )

        for task in pending_tasks:
            parser_record = self.parse_task_record(task)
            self.append_parser_record(parser_record)

            if self.should_flush_batch():
                summary = self.flush_batch(reason="threshold")
                print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
                yield summary

        if self.batch_records:
            summary = self.flush_batch(reason="finished")
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
            yield summary

    def ensure_bucket(self) -> None:
        """Create the configured MinIO bucket if local bootstrap has not done it."""

        if not self.minio_client.bucket_exists(self.minio_config.bucket_name):
            self.minio_client.make_bucket(self.minio_config.bucket_name)

    def parse_task_record(self, task: PendingParseTask) -> dict[str, object | None]:
        """Load one raw snapshot and return a complete parser record JSON object."""

        try:
            response = self.build_response_from_storage_path(
                storage_path=task.storage_path,
                response_url=self.absolute_task_url(task.task_url),
            )
            extracted_data = self.extract_page_data(response)
            return self.build_parser_record(
                task_id=task.task_id,
                extracted_data=extracted_data,
            )
        except Exception as exc:
            self.logger.exception("Failed to parse task_id=%s", task.task_id)
            return self.build_error_record(
                task_id=task.task_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

    def build_response_from_storage_path(
        self,
        storage_path: str,
        response_url: str,
    ) -> TextResponse:
        """Load a gzip HTML object from MinIO and wrap it as a Scrapy response."""

        bucket_name, object_name = split_storage_path(storage_path)
        stored_response = self.minio_client.get_object(bucket_name, object_name)
        try:
            payload = stored_response.read()
        finally:
            stored_response.close()
            stored_response.release_conn()

        if object_name.endswith(".gz"):
            payload = gzip.decompress(payload)

        return TextResponse(
            url=response_url,
            body=payload,
            encoding="utf-8",
        )

    def extract_page_data(self, response) -> dict[str, str]:
        """Extract price, phone, building, and room data from one detail response."""

        data: dict[str, str] = {}

        renting_price = safe_extract(response.css(".property_view_note-emphasis"))
        others_price_container = response.css(
            ".property_view_note-list span:not([class]), "
            ".property_view_note-list span[class='']"
        )
        others_price_data = self.extract_key_value_texts(
            safe_extract(price).replace("\xa0", "")
            for price in others_price_container
        )
        data.update(
            {
                "家賃": renting_price,
                **others_price_data,
            }
        )

        phone_number = safe_extract(response.css(".viewform_advance_shop-cal-number"))
        data.update({"電話番号": phone_number})

        building_info_container = response.css("table.property_view_table")
        data.update(self.extract_table_data(building_info_container))

        room_info_container = response.css("table.data_table")
        data.update(self.extract_table_data(room_info_container))

        return data

    def build_parser_record(
        self,
        task_id: int,
        extracted_data: dict[str, str],
    ) -> dict[str, object | None]:
        """Build a fixed-shape JSON parser record from extracted page data."""

        record = self.empty_parser_record(task_id=task_id)
        for key, value in extracted_data.items():
            if key in record:
                record[key] = null_if_empty(value)
            else:
                self.logger.debug("Ignoring extracted SUUMO field outside schema: %s", key)

        is_valid, error_type, error_message = self.validate_parser_record(record)
        record["is_valid"] = is_valid
        record["error_type"] = error_type
        record["error_message"] = error_message
        if is_valid:
            record["data_hash"] = suumo_data_hash(record)

        return record

    def build_error_record(
        self,
        task_id: int,
        error_type: str,
        error_message: str,
    ) -> dict[str, object | None]:
        """Build a fixed-shape parser record for parse/runtime failures."""

        record = self.empty_parser_record(task_id=task_id)
        record["is_valid"] = False
        record["error_type"] = error_type
        record["error_message"] = error_message[:4000]
        return record

    def empty_parser_record(self, task_id: int) -> dict[str, object | None]:
        """Return a parser record with every schema key present."""

        record = {field_name: None for field_name in PARSER_RECORD_FIELD_NAMES}
        record["task_id"] = task_id
        record["parsed_at"] = datetime.now(timezone.utc).isoformat()
        record["is_valid"] = False
        return record

    def validate_parser_record(
        self,
        record: dict[str, object | None],
    ) -> tuple[bool, str | None, str | None]:
        """Validate the minimum fields needed before loader receives a record."""

        extracted_source_values = [
            record.get(field_name)
            for field_name in SUUMO_SOURCE_FIELD_NAMES
        ]
        if not any(extracted_source_values):
            return False, "ValidationError", "No SUUMO detail fields extracted"

        return True, None, None

    def append_parser_record(self, parser_record: dict[str, object | None]) -> None:
        """Add one parser record to the in-memory batch buffer."""

        if not self.batch_records:
            self.batch_started_at = datetime.now(timezone.utc)

        self.batch_records.append(parser_record)

    def should_flush_batch(self) -> bool:
        """Return true when the buffer exceeds size or age thresholds."""

        if not self.batch_records:
            return False
        if len(self.batch_records) >= self.batch_size:
            return True
        if self.batch_started_at is None:
            return False

        elapsed = datetime.now(timezone.utc) - self.batch_started_at
        return elapsed >= timedelta(seconds=self.batch_seconds)

    def flush_batch(self, reason: str) -> dict[str, object]:
        """Upload the buffered parser record array and persist load_batches."""

        if not self.batch_records:
            raise ValueError("No parser records are buffered")

        metadata_repository = self.require_metadata_repository()
        records = list(self.batch_records)
        task_ids = [int(record["task_id"]) for record in records if record["task_id"] is not None]
        if not task_ids:
            raise ValueError("Buffered parser records do not contain task_id values")

        created_at = datetime.now(timezone.utc)
        batch_id = metadata_repository.reserve_load_batch_id()
        target = build_batch_target(
            created_at=created_at,
            extension=".json",
            bucket_name=self.minio_config.bucket_name,
            compression="gzip",
        )
        payload = json.dumps(
            records,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        stored_object = upload_bytes(
            client=self.minio_client,
            target=target,
            payload=payload,
            content_type="application/json",
            compression="gzip",
        )
        metadata_repository.create_load_batch_and_attach_tasks(
            batch_id=batch_id,
            source_id=self.source_id,
            file_path=stored_object.target.storage_path,
            file_format="json",
            compression=stored_object.compression,
            row_count=len(records),
            file_hash=stored_object.stored_hash,
            task_ids=task_ids,
        )

        self.batch_records.clear()
        self.batch_started_at = None

        return {
            "batch_id": batch_id,
            "file_path": stored_object.target.storage_path,
            "object_name": stored_object.target.object_name,
            "file_format": "json",
            "compression": stored_object.compression,
            "row_count": len(records),
            "file_hash": stored_object.stored_hash,
            "stored_length": stored_object.stored_length,
            "task_ids": task_ids,
            "reason": reason,
            "status": "pending",
        }

    def extract_table_data(self, table_selector) -> dict[str, str]:
        """Convert a two-column SUUMO table into key-value text data."""

        titles = [safe_extract(th) for th in table_selector.css("th")]
        values = [safe_extract(td) for td in table_selector.css("td")]
        return {
            title: value
            for title, value in zip(titles, values, strict=False)
            if title
        }

    def extract_key_value_texts(self, raw_values) -> dict[str, str]:
        """Parse Japanese price labels like 管理費・共益費: value."""

        extracted_values = {}
        for raw_value in raw_values:
            normalized_value = raw_value.strip()
            if not normalized_value:
                continue

            separator = "：" if "：" in normalized_value else ":"
            if separator not in normalized_value:
                self.logger.debug("Skipping non key-value price text: %s", raw_value)
                continue

            key, value = normalized_value.split(separator, maxsplit=1)
            normalized_key = key.strip().replace("・", "_")
            if normalized_key:
                extracted_values[normalized_key] = value.strip()

        return extracted_values

    def absolute_task_url(self, task_url: str) -> str:
        """Return an absolute URL for Scrapy's TextResponse wrapper."""

        if task_url.startswith("http://") or task_url.startswith("https://"):
            return task_url
        if task_url.startswith("/"):
            return f"{self.source_base_url.rstrip('/')}{task_url}"

        return f"{self.source_base_url.rstrip('/')}/{task_url}"

    def require_metadata_repository(self) -> CrawlerMetadataRepository:
        """Return the initialized DB repository or fail loudly."""

        if self.metadata_repository is None:
            raise RuntimeError("Metadata repository is not initialized")

        return self.metadata_repository
