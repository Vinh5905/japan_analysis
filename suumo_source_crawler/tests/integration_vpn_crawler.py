"""Release-image acceptance with a localhost HTTP server and disposable QA DB.
Every download handler rewrites to localhost; no SUUMO traffic or VPN startup.
"""

from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import uuid

import psycopg
from psycopg import sql
from scrapy.utils.reactor import install_reactor

install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
from scrapy import Spider, Request
from scrapy.crawler import CrawlerRunner
from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from twisted.internet import reactor, defer

counts = Counter()


class Server(BaseHTTPRequestHandler):
    """Provide a redirect, retry, connection failure, pagination and cacheable HTML."""

    def log_message(self, *args):
        """Keep QA logs free of request noise."""

    def do_GET(self):
        """Count actual local HTTP requests and return the requested test outcome."""
        counts[self.path] += 1
        if self.path == "/failure":
            self.connection.close()
            return
        code = (
            302
            if self.path == "/redirect"
            else 500
            if self.path == "/retry" and counts[self.path] == 1
            else 200
        )
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/html")
        self.send_header("Content-Type", "text/html")
        self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        self.wfile.write(b"<html>local QA</html>")


server = ThreadingHTTPServer(("127.0.0.1", 0), Server)
threading.Thread(target=server.serve_forever, daemon=True).start()
port = server.server_address[1]


class LocalHandler:
    """Rewrite inside the handler, after accounting, for both supported Scrapy APIs."""

    lazy = True

    def __init__(self, crawler):
        """Wrap the actual HTTP downloader while avoiding all external traffic."""
        self.crawler = crawler
        self.inner = HTTP11DownloadHandler.from_crawler(crawler)

    @classmethod
    def from_crawler(cls, crawler):
        """Construct this isolated downloader."""
        return cls(crawler)

    def local(self, request):
        """Retain path/meta while routing directly to the local server."""
        from urllib.parse import urlsplit

        return request.replace(
            url=f"http://127.0.0.1:{port}" + urlsplit(request.url).path
        )

    async def download_request(self, request):
        """Use the coroutine HTTP handler API shared by Scrapy 2.17 and 2.19."""
        response = await self.inner.download_request(self.local(request))
        return response.replace(url=request.url)

    async def close(self):
        """Release sockets owned by the wrapped downloader."""
        await self.inner.close()


class Pages(Spider):
    """Exercise actual Scrapy pagination, redirect, retry, dedupe and cache paths."""

    name = "suumo_links"

    async def start(self):
        """Request all test outcomes sequentially through the real middleware chain."""
        for path in ("page", "page2", "redirect", "retry", "failure", "cached"):
            yield Request("http://suumo.jp/" + path, callback=self.parse)
        yield Request("http://example.com/other", callback=self.parse)

    def parse(self, response):
        """Schedule one duplicate and one cache hit without causing more network calls."""
        if response.url.endswith("/page"):
            yield Request("http://suumo.jp/page2", callback=self.parse)
        if response.url.endswith("/cached") and not response.meta.get("again"):
            yield Request(
                response.url,
                callback=self.parse,
                dont_filter=True,
                meta={"again": True},
            )


class Claimed(Spider):
    """Reject the duplicate HTML task before request accounting."""

    name = "suumo_html"

    async def start(self):
        """Force the duplicate past the scheduler to exercise the claim middleware."""
        for _ in range(2):
            yield Request(
                "http://suumo.jp/claimed", dont_filter=True, callback=self.parse
            )

    def claim_task_for_request(self, request):
        """Allow exactly one task in this QA spider."""
        if getattr(self, "claimed", False):
            return None
        self.claimed = True
        return 1

    def parse(self, response):
        """No parser work is needed for the downloader assertion."""
        return []


class Fatal(Spider):
    """Prove invalid VPN context stops before any HTTP request reaches the server."""

    name = "fatal_qa"

    async def start(self):
        """Submit a request with a now-completed crawl context."""
        yield Request("http://suumo.jp/blocked")


original_db = os.environ["POSTGRES_DB"]
qa = "vpn_image_qa_" + uuid.uuid4().hex[:12]
kwargs = {
    k: os.environ[v]
    for k, v in {
        "host": "POSTGRES_HOST",
        "user": "POSTGRES_USER",
        "password": "POSTGRES_PASSWORD",
    }.items()
}
admin = psycopg.connect(dbname=original_db, autocommit=True, **kwargs)
admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(qa)))
os.environ["POSTGRES_DB"] = qa
conn = psycopg.connect(dbname=qa, autocommit=True, **kwargs)
conn.execute(
    Path("/app/docker/postgres/init/001_create_crawler_metadata.sql").read_text()
)
vid = conn.execute(
    "INSERT INTO crawl_vpns(filename,relative_path,sha256) VALUES('qa.ovpn','qa.ovpn',%s) RETURNING vpn_id",
    ("a" * 64,),
).fetchone()[0]
rid = conn.execute(
    "INSERT INTO crawl_runs(vpn_id,pipeline_status) VALUES(%s,'running') RETURNING run_id",
    (vid,),
).fetchone()[0]
conn.execute(
    "INSERT INTO crawl_vpn_attempts(run_id,vpn_id,snapshot,status) VALUES(%s,%s,'{}','success')",
    (rid, vid),
)
os.environ.update(
    SUUMO_RUN_ID=str(rid), SUUMO_VPN_ID=str(vid), SUUMO_REQUIRE_VPN_CONTEXT="true"
)
failure = []


@defer.inlineCallbacks
def exercise():
    """Compare durable totals to real local requests, then check fail-closed behavior."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["TELEGRAM_SUMMARY_DIR"] = tmp
            settings = {
                "LOG_ENABLED": False,
                "CONCURRENT_REQUESTS": 1,
                "RETRY_TIMES": 1,
                "DOWNLOAD_TIMEOUT": 2,
                "HTTPCACHE_ENABLED": True,
                "HTTPCACHE_DIR": tmp + "/cache",
                "HTTPCACHE_IGNORE_HTTP_CODES": [500, 302],
                "DOWNLOAD_HANDLERS": {
                    "http": "__main__.LocalHandler",
                    "https": "__main__.LocalHandler",
                },
                "DOWNLOADER_MIDDLEWARES": {
                    "crawler.vpn_accounting.VpnRequestAccounting": 950,
                    "crawler.middlewares.SuumoHtmlTaskClaimMiddleware": 410,
                },
                "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            }
            runner = CrawlerRunner(settings)
            pages = runner.create_crawler(Pages)
            yield runner.crawl(pages)
            assert counts["/retry"] == 2 and counts["/failure"] == 2, (
                dict(counts),
                pages.stats.get_stats(),
            )
            assert counts["/redirect"] == 1 and counts["/html"] == 1, dict(counts)
            assert counts["/page2"] == 1 and counts["/cached"] == 1, dict(counts)
            total = conn.execute(
                "SELECT total_requests FROM crawl_vpns WHERE vpn_id=%s", (vid,)
            ).fetchone()[0]
            assert total == sum(counts.values()) - counts["/other"] == 9, (
                total,
                counts,
            )
            yield runner.crawl(Claimed)
            assert counts["/claimed"] == 1, counts
            assert (
                conn.execute(
                    "SELECT total_requests FROM crawl_vpns WHERE vpn_id=%s", (vid,)
                ).fetchone()[0]
                == 10
            )
            conn.execute(
                "UPDATE crawl_runs SET pipeline_status='completed' WHERE run_id=%s",
                (rid,),
            )
            crawler = runner.create_crawler(Fatal)
            yield runner.crawl(crawler)
            assert counts["/blocked"] == 0, counts
            assert (
                crawler.stats.get_value("finish_reason") == "vpn_accounting_failed"
            ), crawler.stats.get_stats()
            assert (Path(tmp) / str(rid) / "vpn_accounting_failed").exists()
            print(
                "PASS: pagination + redirects + retries + failed downloads = 9 requests; cache/filter/internal excluded; task claim = 1; invalid context stops network"
            )
    except Exception as exc:
        failure.append(exc)
    finally:
        reactor.stop()


reactor.callWhenRunning(exercise)
try:
    reactor.run()
finally:
    server.shutdown()
    conn.close()
    admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(qa)))
    admin.close()
    os.environ["POSTGRES_DB"] = original_db
if failure:
    raise failure[0]
