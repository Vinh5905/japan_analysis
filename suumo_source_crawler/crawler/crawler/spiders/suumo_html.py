from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import scrapy
from scrapy import signals

from crawler.metadata_db import CrawlerMetadataRepository, RawSnapshotRecord
from crawler.object_storage import create_minio_client, load_minio_config
from crawler.storage import (
    build_raw_snapshot_target,
    normalize_task_url,
    task_url_hash,
    upload_bytes,
)


class SuumoHtmlSpider(scrapy.Spider):
    """Fetch SUUMO detail pages, upload compressed HTML, and persist metadata."""

    name = "suumo_html"
    allowed_domains = ["suumo.jp"]

    def __init__(self, *args, **kwargs):
        """Initialize settings-backed runtime state for HTML crawl persistence."""

        super().__init__(*args, **kwargs)
        self.links_file_path = Path("tmp/suumo_links.txt")
        self.link_limit = 0
        self.source_id = 1
        self.created_by = "schedule"
        self.run_id: int | None = None
        self.run_created_at: datetime | None = None
        self.metadata_repository: CrawlerMetadataRepository | None = None
        self.minio_config = load_minio_config()
        self.minio_client = create_minio_client(self.minio_config)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Create the spider and load DB-backed crawl settings."""

        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.links_file_path = Path(
            crawler.settings.get("SUUMO_HTML_LINKS_FILE", "tmp/suumo_links.txt")
        )
        spider.link_limit = crawler.settings.getint("SUUMO_HTML_LINK_LIMIT", 0)
        spider.source_id = crawler.settings.getint("SUUMO_SOURCE_ID", 1)
        spider.created_by = crawler.settings.get("SUUMO_RUN_CREATED_BY", "schedule")
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)
        return spider

    def open_spider(self, spider):
        """Open DB resources and create the crawl_runs row for this spider run."""

        self.metadata_repository = CrawlerMetadataRepository.from_env()
        crawl_run = self.metadata_repository.create_crawl_run(
            source_id=self.source_id,
            created_by=self.created_by,
        )
        self.run_id = crawl_run.run_id
        self.run_created_at = crawl_run.created_at
        self.logger.info("Created crawl_run row with run_id=%s", self.run_id)

    def close_spider(self, spider, reason):
        """Set crawl_runs.finished_at and close DB resources."""

        if self.metadata_repository is None:
            return

        try:
            if self.run_id is not None:
                finalized_tasks = self.metadata_repository.finalize_unfinished_run_tasks(
                    run_id=self.run_id,
                    error_type="SpiderClosed",
                    error_message=f"Spider closed before task finished: {reason}",
                )
                if finalized_tasks:
                    self.logger.info(
                        "Finalized %s unfinished crawl_tasks rows for run_id=%s",
                        finalized_tasks,
                        self.run_id,
                    )
                self.metadata_repository.finish_crawl_run(self.run_id)
                self.logger.info(
                    "Finished crawl_run row with run_id=%s reason=%s",
                    self.run_id,
                    reason,
                )
        finally:
            self.metadata_repository.close()
            self.metadata_repository = None

    async def start(self):
        """Read tmp links and schedule deduplicated URLs for HTML storage."""

        links = self.read_links()
        if not links:
            self.logger.warning("No SUUMO links found in %s", self.links_file_path)
            return

        candidate_links = self.filter_new_task_links(links)
        selected_links = self.select_links(candidate_links)
        if not selected_links:
            self.logger.warning("No new SUUMO links found in %s", self.links_file_path)
            return

        self.ensure_bucket()
        self.logger.info(
            "Uploading HTML for %s/%s new SUUMO links to MinIO bucket %s with run_id=%s",
            len(selected_links),
            len(candidate_links),
            self.minio_config.bucket_name,
            self.run_id,
        )

        for url in selected_links:
            yield scrapy.Request(
                url,
                callback=self.parse_page,
                errback=self.handle_request_error,
                cb_kwargs={
                    "requested_url": url,
                },
                meta={"handle_httpstatus_all": True},
            )

    def read_links(self) -> list[str]:
        """Read unique non-empty SUUMO detail URLs from the temporary links file."""

        if not self.links_file_path.exists():
            return []

        links = []
        seen_links = set()
        for raw_line in self.links_file_path.read_text(encoding="utf-8").splitlines():
            link = raw_line.strip()
            if not link or link in seen_links:
                continue
            links.append(link)
            seen_links.add(link)

        return links

    def select_links(self, links: list[str]) -> list[str]:
        """Apply the optional SUUMO_HTML_LINK_LIMIT setting to new links."""

        if self.link_limit <= 0:
            return links

        return links[: self.link_limit]

    def filter_new_task_links(self, links: list[str]) -> list[str]:
        """Deduplicate candidate links by url_hash before claiming run tasks."""

        candidate_links = []
        seen_hashes = set()
        for link in links:
            url_hash = task_url_hash(link)
            if url_hash in seen_hashes:
                continue
            candidate_links.append(link)
            seen_hashes.add(url_hash)

        return candidate_links

    def ensure_bucket(self) -> None:
        """Create the configured MinIO bucket if local bootstrap has not done it."""

        if not self.minio_client.bucket_exists(self.minio_config.bucket_name):
            self.minio_client.make_bucket(self.minio_config.bucket_name)

    def claim_task_for_request(self, request) -> int | None:
        """Create one crawl_tasks row when the downloader starts a request."""

        metadata_repository = self.require_metadata_repository()
        requested_url = request.cb_kwargs.get("requested_url", request.url)
        return metadata_repository.create_run_task(
            run_id=self.require_run_id(),
            task_url=normalize_task_url(requested_url),
            url_hash=task_url_hash(requested_url),
            method=request.method,
            scheduled_at=datetime.now(timezone.utc),
        )

    def parse_page(
        self,
        response,
        task_id: int,
        requested_url: str,
    ):
        """Upload one detail page and persist raw/task metadata."""

        if response.status < 200 or response.status >= 300:
            result = self.mark_failed_task_result(
                task_id=task_id,
                requested_url=requested_url,
                error_type="HttpStatusError",
                error_message=f"Unexpected HTTP status {response.status}",
            )
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
            yield result
            return

        try:
            upload_result = self.store_successful_response(
                response=response,
                task_id=task_id,
                requested_url=requested_url,
            )
        except Exception as exc:
            self.logger.exception("Failed to persist SUUMO HTML for %s", requested_url)
            upload_result = self.mark_failed_task_result(
                task_id=task_id,
                requested_url=requested_url,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

        print(json.dumps(upload_result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        yield upload_result

    def handle_request_error(self, failure):
        """Persist failed crawl_tasks rows after Scrapy exhausts retries."""

        request = failure.request
        task_id = request.cb_kwargs.get("task_id")
        if task_id is None:
            self.logger.info("Ignoring request failure before task claim: %s", request.url)
            return

        requested_url = request.cb_kwargs.get("requested_url", request.url)
        result = self.mark_failed_task_result(
            task_id=task_id,
            requested_url=requested_url,
            error_type=failure.type.__name__,
            error_message=str(failure.value),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        yield result

    def store_successful_response(
        self,
        response,
        task_id: int,
        requested_url: str,
    ) -> dict[str, object]:
        """Upload response bytes and update the existing task to pending."""

        metadata_repository = self.require_metadata_repository()
        run_id = self.require_run_id()
        run_created_at = self.require_run_created_at()
        raw_snapshot_id = metadata_repository.reserve_raw_snapshot_id()
        content_type = self.extract_content_type(response)
        target = build_raw_snapshot_target(
            created_at=run_created_at,
            run_id=run_id,
            raw_snapshot_id=raw_snapshot_id,
            content_type=content_type,
            bucket_name=self.minio_config.bucket_name,
            compression="gzip",
        )
        stored_object = upload_bytes(
            client=self.minio_client,
            target=target,
            payload=response.body,
            content_type=content_type,
            compression="gzip",
        )

        task_url = normalize_task_url(requested_url)
        fetched_at = datetime.now(timezone.utc)
        metadata_repository.mark_task_pending_with_snapshot(
            task_id=task_id,
            fetched_at=fetched_at,
            snapshot=RawSnapshotRecord(
                raw_snapshot_id=raw_snapshot_id,
                url=task_url,
                final_url=self.extract_final_url(requested_url, response.url),
                http_status=response.status,
                content_type=content_type,
                content_length=stored_object.content_length,
                content_hash=stored_object.content_hash,
                storage_path=stored_object.target.storage_path,
                compression=stored_object.compression,
                encoding=response.encoding,
            ),
        )

        return {
            "source_url": response.url,
            "http_status": response.status,
            "run_id": run_id,
            "task_id": task_id,
            "raw_snapshot_id": raw_snapshot_id,
            "storage_path": stored_object.target.storage_path,
            "object_name": stored_object.target.object_name,
            "content_type": content_type,
            "content_length": stored_object.content_length,
            "content_hash": stored_object.content_hash,
            "compression": stored_object.compression,
            "stored_length": stored_object.stored_length,
            "status": "pending",
        }

    def mark_failed_task_result(
        self,
        task_id: int,
        requested_url: str,
        error_type: str,
        error_message: str,
    ) -> dict[str, object]:
        """Update the current task to failed and return printable metadata."""

        metadata_repository = self.require_metadata_repository()
        run_id = self.require_run_id()
        metadata_repository.mark_task_failed(
            task_id=task_id,
            error_type=error_type,
            error_message=error_message,
        )
        return {
            "source_url": requested_url,
            "run_id": run_id,
            "task_id": task_id,
            "status": "failed",
            "error_type": error_type,
            "error_message": error_message,
        }

    def extract_content_type(self, response) -> str:
        """Return a supported raw_content_type_enum value from response headers."""

        raw_header = response.headers.get(b"Content-Type", b"text/html").decode(
            "latin1",
            errors="ignore",
        )
        media_type = raw_header.split(";", maxsplit=1)[0].strip().lower()
        if media_type in {"application/json", "text/html"}:
            return media_type

        self.logger.warning(
            "Unsupported content type %r for %s; storing as text/html",
            raw_header,
            response.url,
        )
        return "text/html"

    def extract_final_url(self, requested_url: str, response_url: str) -> str | None:
        """Return normalized final URL only when redirect changed the URL."""

        normalized_requested_url = normalize_task_url(requested_url)
        normalized_response_url = normalize_task_url(response_url)
        if normalized_response_url == normalized_requested_url:
            return None

        return normalized_response_url

    def require_metadata_repository(self) -> CrawlerMetadataRepository:
        """Return the initialized DB repository or fail loudly."""

        if self.metadata_repository is None:
            raise RuntimeError("Metadata repository is not initialized")

        return self.metadata_repository

    def require_run_id(self) -> int:
        """Return the current crawl run id or fail loudly."""

        if self.run_id is None:
            raise RuntimeError("crawl_runs row has not been created")

        return self.run_id

    def require_run_created_at(self) -> datetime:
        """Return the current crawl run created_at timestamp or fail loudly."""

        if self.run_created_at is None:
            raise RuntimeError("crawl_runs row has not been created")

        return self.run_created_at
