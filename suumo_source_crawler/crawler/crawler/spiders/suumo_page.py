from __future__ import annotations

import gzip
import json
from pathlib import Path
from urllib.parse import urlparse

import scrapy
from scrapy.http import TextResponse

from crawler.object_storage import create_minio_client, split_storage_path


def safe_extract(selector) -> str:
    """Extract normalized visible text from a Scrapy selector or selector list."""

    text = selector.xpath("string()").get()
    return text.strip().replace("\t", "") if text else ""


class SuumoPageSpider(scrapy.Spider):
    """Extract one or more SUUMO detail pages from the temporary link file."""

    name = "suumo_page"
    allowed_domains = ["suumo.jp"]

    def __init__(self, *args, **kwargs):
        """Initialize settings-backed defaults for local parser checks."""

        super().__init__(*args, **kwargs)
        self.links_file_path = Path("tmp/suumo_links.txt")
        self.link_limit = 1
        self.storage_path = ""
        self.storage_source_url = ""
        self.minio_client = create_minio_client()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Create the spider and load tmp file settings from Scrapy settings."""

        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.links_file_path = Path(
            crawler.settings.get("SUUMO_PAGE_LINKS_FILE", "tmp/suumo_links.txt")
        )
        spider.link_limit = crawler.settings.getint("SUUMO_PAGE_LINK_LIMIT", 1)
        spider.storage_path = crawler.settings.get("SUUMO_PAGE_STORAGE_PATH", "")
        spider.storage_source_url = crawler.settings.get("SUUMO_PAGE_SOURCE_URL", "")
        return spider

    async def start(self):
        """Read links from tmp and schedule only the configured number of pages."""

        if self.storage_path:
            self.logger.info("Loading SUUMO page HTML from MinIO path %s", self.storage_path)
            response = self.build_response_from_storage_path(self.storage_path)
            for result in self.parse_page(response):
                yield result
            return

        links = self.read_links()
        if not links:
            self.logger.warning("No SUUMO links found in %s", self.links_file_path)
            return

        selected_links = links[: self.link_limit]
        self.logger.info(
            "Starting SUUMO page extraction for %s/%s links from %s",
            len(selected_links),
            len(links),
            self.links_file_path,
        )

        for url in selected_links:
            yield scrapy.Request(url, callback=self.parse_page)

    def read_links(self) -> list[str]:
        """Read non-empty SUUMO detail URLs from the temporary links file."""

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

    def parse_page(self, response):
        """Extract SUUMO detail fields and print them as JSON for manual checking."""

        self.logger.debug(
            "SUUMO page response status=%s url=%s price_nodes=%s property_tables=%s data_tables=%s",
            response.status,
            response.url,
            len(response.css(".property_view_note-emphasis")),
            len(response.css("table.property_view_table")),
            len(response.css("table.data_table")),
        )
        data = self.extract_page_data(response)
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), flush=True)
        yield data

    def build_response_from_storage_path(self, storage_path: str) -> TextResponse:
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

        response_url = self.storage_source_url or storage_path
        return TextResponse(
            url=response_url,
            body=payload,
            encoding="utf-8",
        )

    def extract_page_data(self, response) -> dict[str, str]:
        """Extract price, phone, building, and room data from one detail response."""

        data: dict[str, str] = {}

        data.update({"id": self.extract_response_id(response)})

        renting_price = safe_extract(response.css(".property_view_note-emphasis"))
        others_price_container = response.css(
            ".property_view_note-list span:not([class]), "
            ".property_view_note-list span[class='']"
        )
        others_price_data = self.extract_key_value_texts(
            safe_extract(price).replace("\xa0", "")
            for price in others_price_container
        )
        price_data = {
            "家賃": renting_price,
            **others_price_data,
        }
        data.update(price_data)

        phone_number = safe_extract(response.css(".viewform_advance_shop-cal-number"))
        data.update({"電話番号": phone_number})

        building_info_container = response.css("table.property_view_table")
        building_info_data = self.extract_table_data(building_info_container)
        data.update(building_info_data)

        room_info_container = response.css("table.data_table")
        room_info_data = self.extract_table_data(room_info_container)
        data.update(room_info_data)

        return data

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

    def extract_response_id(self, response) -> str:
        """Extract the SUUMO listing id from hidden fields or the response URL."""

        hidden_jnc = response.css("input[name='jnc']::attr(value)").get()
        if hidden_jnc:
            return f"jnc_{hidden_jnc.strip()}"

        canonical_url = response.css("link[rel='canonical']::attr(href)").get()
        return self.extract_id(canonical_url or response.url)

    def extract_id(self, url: str) -> str:
        """Extract the SUUMO listing id from a detail page URL path."""

        path_parts = [part for part in urlparse(url).path.split("/") if part]
        if not path_parts:
            return url

        last_part = path_parts[-1]
        if last_part.startswith("bc_"):
            return last_part.removeprefix("bc_")

        return last_part
