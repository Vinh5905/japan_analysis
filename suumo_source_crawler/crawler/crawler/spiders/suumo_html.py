from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import scrapy

from crawler.object_storage import create_minio_client, load_minio_config
from crawler.storage import build_raw_snapshot_target, upload_bytes


class SuumoHtmlSpider(scrapy.Spider):
    """Fetch SUUMO detail pages and upload compressed HTML to MinIO."""

    name = "suumo_html"
    allowed_domains = ["suumo.jp"]

    def __init__(self, *args, **kwargs):
        """Initialize demo-only IDs until database persistence is added."""

        super().__init__(*args, **kwargs)
        self.links_file_path = Path("tmp/suumo_links.txt")
        self.link_limit = 1
        self.raw_snapshot_start_id = 1
        self.run_started_at = datetime.now(timezone.utc)
        self.run_id = int(self.run_started_at.strftime("%Y%m%d%H%M%S"))
        self.minio_config = load_minio_config()
        self.minio_client = create_minio_client(self.minio_config)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Create the spider and load demo settings from Scrapy settings."""

        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.links_file_path = Path(
            crawler.settings.get("SUUMO_HTML_LINKS_FILE", "tmp/suumo_links.txt")
        )
        spider.link_limit = crawler.settings.getint("SUUMO_HTML_LINK_LIMIT", 1)
        spider.raw_snapshot_start_id = crawler.settings.getint(
            "SUUMO_HTML_RAW_SNAPSHOT_START_ID",
            1,
        )

        configured_run_id = crawler.settings.get("SUUMO_HTML_RUN_ID")
        if configured_run_id:
            spider.run_id = int(configured_run_id)

        return spider

    async def start(self):
        """Read links from tmp and schedule the configured demo batch."""

        links = self.read_links()
        if not links:
            self.logger.warning("No SUUMO links found in %s", self.links_file_path)
            return

        selected_links = links[: self.link_limit]
        self.ensure_bucket()
        self.logger.info(
            "Uploading HTML for %s/%s SUUMO links to MinIO bucket %s with demo run_id=%s",
            len(selected_links),
            len(links),
            self.minio_config.bucket_name,
            self.run_id,
        )

        for offset, url in enumerate(selected_links):
            raw_snapshot_id = self.raw_snapshot_start_id + offset
            yield scrapy.Request(
                url,
                callback=self.parse_page,
                cb_kwargs={"raw_snapshot_id": raw_snapshot_id},
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

    def ensure_bucket(self) -> None:
        """Create the configured MinIO bucket if local bootstrap has not done it."""

        if not self.minio_client.bucket_exists(self.minio_config.bucket_name):
            self.minio_client.make_bucket(self.minio_config.bucket_name)

    def parse_page(self, response, raw_snapshot_id: int):
        """Upload one detail page response body as gzip-compressed HTML."""

        target = build_raw_snapshot_target(
            created_at=self.run_started_at,
            run_id=self.run_id,
            raw_snapshot_id=raw_snapshot_id,
            content_type="text/html",
            bucket_name=self.minio_config.bucket_name,
            compression="gzip",
        )
        stored_object = upload_bytes(
            client=self.minio_client,
            target=target,
            payload=response.body,
            content_type="text/html",
            compression="gzip",
        )

        upload_result = {
            "source_url": response.url,
            "http_status": response.status,
            "run_id": self.run_id,
            "raw_snapshot_id": raw_snapshot_id,
            "storage_path": stored_object.target.storage_path,
            "object_name": stored_object.target.object_name,
            "content_type": "text/html",
            "content_length": stored_object.content_length,
            "content_hash": stored_object.content_hash,
            "compression": stored_object.compression,
            "stored_length": stored_object.stored_length,
        }
        print(json.dumps(upload_result, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        yield upload_result
