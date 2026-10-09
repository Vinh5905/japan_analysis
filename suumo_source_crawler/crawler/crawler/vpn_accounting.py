"""Count SUUMO downloader attempts durably, after filters and HTTP cache."""
import os
from pathlib import Path
from urllib.parse import urlsplit
import uuid

import psycopg
from scrapy import signals
from scrapy.exceptions import IgnoreRequest

from crawler.metadata_db import connect_postgres


class VpnRequestAccounting:
    """Require verified release context and stop downloads if accounting fails."""

    def __init__(self, crawler):
        """Store pipeline context without opening a DB for local offline parsers."""
        self.crawler = crawler
        self.run_id = os.environ.get('SUUMO_RUN_ID', '')
        self.vpn_id = os.environ.get('SUUMO_VPN_ID', '')
        self.required = os.environ.get('SUUMO_REQUIRE_VPN_CONTEXT', '').lower() in {'true','1','yes'}
        self.connection = None
        self.failed = False

    @classmethod
    def from_crawler(cls, crawler):
        """Close the accounting connection when the spider ends."""
        instance = cls(crawler)
        crawler.signals.connect(instance.close, signal=signals.spider_closed)
        return instance

    def close(self, **kwargs):
        """Release this middleware's independent autocommit connection."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def record(self, request_id, stage):
        """Retry an unknown DB commit with the same UUID, never increment twice."""
        for attempt in range(2):
            try:
                if self.connection is None:
                    self.connection = connect_postgres()
                    self.connection.execute("SET statement_timeout='5s'; SET lock_timeout='2s'")
                self.connection.execute('SELECT record_crawl_vpn_request(%s,%s,%s,%s)',
                                        (request_id, int(self.run_id), int(self.vpn_id), stage)).fetchone()
                return
            except psycopg.OperationalError:
                self.close()
                if attempt:
                    raise

    def abort(self, spider):
        """Persist a fatal marker before asking Scrapy to close and rejecting downloads."""
        self.failed = True
        self.crawler.stats.set_value('vpn/accounting_failed', True)
        root = os.environ.get('TELEGRAM_SUMMARY_DIR')
        try:
            if root and self.run_id.isdigit():
                directory = Path(root) / self.run_id
                directory.mkdir(parents=True, exist_ok=True)
                (directory / 'vpn_accounting_failed').touch()
        except OSError:
            spider.logger.error('Cannot persist VPN accounting marker')
        finally:
            self.crawler.engine.close_spider(spider, reason='vpn_accounting_failed')

    def process_request(self, request, spider):
        """Count each new download attempt; retry/redirect clones get a fresh UUID."""
        parsed = urlsplit(request.url)
        if parsed.scheme not in {'http','https'} or not (parsed.hostname == 'suumo.jp' or (parsed.hostname or '').endswith('.suumo.jp')):
            return None
        if self.failed:
            raise IgnoreRequest('VPN accounting already failed')
        if not self.required and not self.vpn_id:
            return None  # Local direct downloads have no VPN to attribute.
        try:
            if not self.run_id.isdigit() or not self.vpn_id.isdigit():
                raise ValueError('Verified VPN context missing')
            self.record(uuid.uuid4(), spider.name)
            self.crawler.stats.inc_value('vpn/request_count')
        except Exception as exc:
            # Do not log DB exceptions: they can contain connection credentials.
            spider.logger.error('VPN accounting failed (%s)', type(exc).__name__)
            try:
                self.abort(spider)
            finally:
                raise IgnoreRequest('VPN accounting failed; pipeline stopped')
        return None
