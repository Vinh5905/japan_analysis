from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import scrapy
from scrapy import signals

from crawler.metadata_db import CrawlerMetadataRepository
from crawler.storage import task_url_hash


class SuumoLinksSpider(scrapy.Spider):
    """Collect listing detail URLs from all SUUMO search result pages."""

    name = "suumo_links"
    allowed_domains = ["suumo.jp"]

    base_url = (
        "https://suumo.jp/jj/chintai/ichiran/FR301FC001/"
        "?ar=060&bs=040&ta=27&sc=27123&cb=0.0&ct=9999999&et=9999999"
        "&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="
    )
    output_path = Path("tmp/suumo_links.txt")
    listing_link_selector = "div#js-bukkenList div.cassetteitem-item a.js-cassette_link_href::attr(href)"
    last_page_selector = "div.pagination_set-nav > ol > li:last-child > a::text"

    def __init__(self, *args, **kwargs):
        """Initialize per-run in-memory state for duplicate detection."""

        super().__init__(*args, **kwargs)
        self.seen_url_hashes: set[str] = set()
        self.metadata_repository: CrawlerMetadataRepository | None = None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Create the spider and connect startup cleanup to Scrapy's signal system."""

        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.open_spider, signal=signals.spider_opened)
        crawler.signals.connect(spider.close_spider, signal=signals.spider_closed)
        return spider

    def open_spider(self, spider):
        """Reset the temporary output file and open the metadata DB connection."""

        self.logger.info("Resetting temporary output file %s", self.output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        # This is intentionally overwritten on each run so parsers read fresh links only.
        self.output_path.write_text("", encoding="utf-8")
        self.seen_url_hashes.clear()
        self.metadata_repository = CrawlerMetadataRepository.from_env()

    def close_spider(self, spider, reason):
        """Close the metadata DB connection after the spider finishes."""

        if self.metadata_repository is not None:
            self.metadata_repository.close()
            self.metadata_repository = None

    async def start(self):
        """Fetch the first result page once to discover the total page count."""

        self.logger.info("Starting SUUMO links spider with base URL: %s", self.base_url)
        yield scrapy.Request(
            self.build_page_url(1),
            callback=self.parse_page_count,
            cb_kwargs={"page_number": 1},
        )

    def build_page_url(self, page_number: int) -> str:
        """Build a SUUMO result page URL while preserving the original query params."""

        parsed_url = urlparse(self.base_url)
        query_params = parse_qs(parsed_url.query, keep_blank_values=True)

        if page_number <= 1:
            query_params.pop("page", None)
        else:
            query_params["page"] = [str(page_number)]

        return urlunparse(
            parsed_url._replace(query=urlencode(query_params, doseq=True))
        )

    def parse_page_count(self, response, page_number: int):
        """Read pagination, then enqueue every known listing page request."""
        last_page_number = self.extract_last_page_number(response)
        self.logger.info("Discovered %s SUUMO result pages", last_page_number)

        # Reuse the bootstrap response for page 1 so the first page is not downloaded twice.
        self.parse_listing_page(response, page_number=page_number)

        for next_page_number in range(2, last_page_number + 1):
            yield scrapy.Request(
                self.build_page_url(next_page_number),
                callback=self.parse_listing_page,
                cb_kwargs={"page_number": next_page_number},
                # Lower page numbers get higher priority so output stays easier to inspect.
                priority=-next_page_number,
            )

    def extract_last_page_number(self, response) -> int:
        """Extract the last page number from SUUMO pagination markup."""

        raw_page_text = response.css(self.last_page_selector).get(default="1").strip()
        page_digits = "".join(char for char in raw_page_text if char.isdigit())

        if not page_digits:
            self.logger.warning(
                "Could not parse last page number from %r; falling back to page 1",
                raw_page_text,
            )
            return 1

        return int(page_digits)

    def parse_listing_page(self, response, page_number: int):
        """Extract listing URLs from one known SUUMO result page."""

        links = self.extract_listing_links(response)
        new_links = self.filter_new_links(links)

        self.logger.info(
            "Page %s returned %s links, %s new links",
            page_number,
            len(links),
            len(new_links),
        )

        if new_links:
            self.write_links(new_links)

    def extract_listing_links(self, response) -> list[str]:
        """Extract and normalize listing detail URLs from the SUUMO result container."""

        container_element = response.css("div#js-bukkenList")
        raw_links = container_element.css(self.listing_link_selector).getall()
        return [response.urljoin(link) for link in raw_links]

    def filter_new_links(self, links: list[str]) -> list[str]:
        """Keep only links whose url_hash has never existed in crawl_tasks."""

        if self.metadata_repository is None:
            raise RuntimeError("Metadata repository is not initialized")

        candidate_links: list[tuple[str, str]] = []
        page_seen_hashes = set()
        for link in links:
            url_hash = task_url_hash(link)
            if url_hash in self.seen_url_hashes or url_hash in page_seen_hashes:
                continue
            candidate_links.append((link, url_hash))
            page_seen_hashes.add(url_hash)

        existing_hashes = self.metadata_repository.fetch_existing_task_hashes(
            url_hash for _, url_hash in candidate_links
        )

        new_links = []
        for link, url_hash in candidate_links:
            if url_hash in existing_hashes:
                continue
            new_links.append(link)
            self.seen_url_hashes.add(url_hash)

        return new_links

    def write_links(self, links: list[str]) -> None:
        """Append newly discovered listing URLs to the temporary output file."""

        with self.output_path.open("a", encoding="utf-8") as output_file:
            for link in links:
                output_file.write(f"{link}\n")
