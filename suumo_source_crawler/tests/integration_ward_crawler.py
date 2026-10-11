"""Run in release image with local DB; no Scrapy network engine or VPN.
Creates a disposable DB, exercises actual repository/spider context and rerun.
"""

import asyncio
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
import uuid
import psycopg
from psycopg import sql
from crawler.metadata_db import CrawlerMetadataRepository
from crawler.spiders.suumo_html import SuumoHtmlSpider
from crawler.spiders.suumo_page import SuumoPageSpider
from crawler.spiders.suumo_links import SuumoLinksSpider
from tools import manual_rerun_failed_html as rerun
from scrapy.crawler import Crawler
from scrapy.settings import Settings

original_db = os.environ["POSTGRES_DB"]
qa = "ward_image_qa_" + uuid.uuid4().hex[:12]
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
try:
    conn = psycopg.connect(dbname=qa, autocommit=True, **kwargs)
    conn.execute(
        Path("/app/docker/postgres/init/001_create_crawler_metadata.sql").read_text()
    )
    wards = conn.execute(
        "SELECT area_id,ward,display_name FROM crawl_areas ORDER BY sc LIMIT 2"
    ).fetchall()
    runs = []
    for area_id, ward, name in wards:
        run_id = conn.execute(
            "INSERT INTO crawl_runs(area_id,pipeline_key,pipeline_status,created_by,area_snapshot) VALUES(%s,%s,'running','manual',%s) RETURNING run_id",
            (
                area_id,
                uuid.uuid4().hex,
                json.dumps(
                    {
                        "prefecture": "大阪府",
                        "municipality": "大阪市",
                        "ward": ward,
                        "display_name": name,
                    }
                ),
            ),
        ).fetchone()[0]
        runs.append(run_id)
        snapshot = conn.execute(
            "INSERT INTO raw_snapshots(url,content_type,content_length,content_hash,storage_path) VALUES('/test','text/html',1,%s,%s) RETURNING raw_snapshot_id",
            ("0" * 64, f"suumo/test/{run_id}"),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO crawl_tasks(run_id,url,url_hash,raw_snapshot_id) VALUES(%s,'/test',%s,%s)",
            (run_id, "1" * 64, snapshot),
        )
        conn.execute(
            "INSERT INTO crawl_tasks(run_id,url,url_hash,status) VALUES(%s,%s,%s,'failed')",
            (run_id, f"/failed/{run_id}", "a" * 63 + str(run_id)),
        )
    repo = CrawlerMetadataRepository(conn)
    assert [t.run_id for t in repo.fetch_pending_parse_tasks(run_id=runs[0])] == [
        runs[0]
    ]
    os.environ["SUUMO_RUN_ID"] = str(runs[0])
    with patch("crawler.spiders.suumo_html.create_minio_client"):
        html = SuumoHtmlSpider()
        html.open_spider(html)
        assert html.run_id == runs[0]
        assert conn.execute("SELECT count(*) FROM crawl_runs").fetchone()[0] == 2
        html.metadata_repository.close()
    conn.execute("UPDATE crawl_runs SET finished_at=now() WHERE run_id=%s", (runs[0],))
    with patch("crawler.spiders.suumo_html.create_minio_client"):
        spider = SuumoHtmlSpider()
        try:
            spider.open_spider(spider)
        except RuntimeError:
            pass
        else:
            raise AssertionError("Closed run was replayed")
        spider.metadata_repository.close()
    # Actual parser start passes only the current run to the repository.
    with patch("crawler.spiders.suumo_page.create_minio_client"):
        page = SuumoPageSpider()
        page.metadata_repository = repo
        seen = []
        page.parse_task_record = lambda task: seen.append(task.run_id) or {}
        page.append_parser_record = lambda record: None
        page.should_flush_batch = lambda: False

        async def consume():
            async for _ in page.start():
                pass

        asyncio.run(consume())
        assert seen == [runs[0]], seen
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "run123/links.txt"
        crawler = Crawler(
            SuumoLinksSpider,
            Settings(
                {
                    "SUUMO_SEARCH_URL": "https://suumo.jp/chintai/?sc=27123",
                    "SUUMO_HTML_LINKS_FILE": str(path),
                }
            ),
        )
        links = SuumoLinksSpider.from_crawler(crawler)
        links.open_spider(links)
        links.write_links(["https://suumo.jp/chintai/jnc_test/"])
        assert path.read_text() == "https://suumo.jp/chintai/jnc_test/\n"
        links.close_spider(links, "test")
        launched = []

        def fake_html(path, source, level, run_id, label):
            a = conn.execute(
                "SELECT area_id FROM crawl_runs WHERE run_id=%s", (run_id,)
            ).fetchone()[0]
            launched.append((a, path.read_text(), label))
            assert len(path.read_text().splitlines()) == 1
            assert label.startswith("大阪府 · 大阪市 · ")
            from subprocess import CompletedProcess

            return CompletedProcess([], 0)

        with (
            patch.object(
                rerun,
                "parse_args",
                return_value=type(
                    "Args",
                    (),
                    {
                        "links_file": str(Path(tmp) / "links.txt"),
                        "report_dir": str(Path(tmp) / "reports"),
                        "source_id": 1,
                        "limit": 0,
                        "dry_run": False,
                        "loglevel": "INFO",
                        "keep_links_file": False,
                    },
                )(),
            ),
            patch.object(rerun, "run_suumo_html", side_effect=fake_html),
        ):
            assert rerun.main() == 0
        assert {a for a, _, _ in launched} == {w[0] for w in wards}
        assert len(launched) == 2
        assert conn.execute("SELECT count(*) FROM crawl_runs").fetchone()[0] == 4
    # Managed rerun must reuse the preflight run and apply LIMIT within its ward.
    vid = conn.execute(
        "INSERT INTO crawl_vpns(filename,relative_path,sha256) VALUES('qa.ovpn','qa.ovpn',%s) RETURNING vpn_id",
        ("a" * 64,),
    ).fetchone()[0]
    managed = conn.execute(
        "INSERT INTO crawl_runs(source_id,area_id,pipeline_key,pipeline_status,vpn_id,created_by) VALUES(1,%s,%s,'running',%s,'manual') RETURNING run_id",
        (wards[1][0], uuid.uuid4().hex, vid),
    ).fetchone()[0]
    conn.execute(
        "INSERT INTO crawl_vpn_attempts(run_id,vpn_id,snapshot,status) VALUES(%s,%s,'{}','success')",
        (managed, vid),
    )
    os.environ.update(
        SUUMO_RUN_ID=str(managed),
        SUUMO_VPN_ID=str(vid),
        SUUMO_REQUIRE_VPN_CONTEXT="true",
    )
    with tempfile.TemporaryDirectory() as tmp:
        args = type(
            "Args",
            (),
            {
                "links_file": str(Path(tmp) / "links.txt"),
                "report_dir": str(Path(tmp) / "reports"),
                "source_id": 1,
                "limit": 1,
                "dry_run": False,
                "loglevel": "INFO",
                "keep_links_file": False,
            },
        )()
        managed_calls = []

        def fake_managed(path, source, level, run_id, label):
            """Assert the retry selects only the second ward despite a global first task."""
            assert run_id == managed
            assert path.read_text().strip().endswith("/failed/" + str(runs[1]))
            managed_calls.append(run_id)
            from subprocess import CompletedProcess

            return CompletedProcess([], 0)

        with (
            patch.object(rerun, "parse_args", return_value=args),
            patch.object(rerun, "run_suumo_html", side_effect=fake_managed),
        ):
            assert rerun.main() == 0
            assert managed_calls == [managed]
            assert conn.execute("SELECT count(*) FROM crawl_runs").fetchone()[0] == 5
            assert (
                conn.execute(
                    "SELECT pipeline_status FROM crawl_runs WHERE run_id=%s", (managed,)
                ).fetchone()[0]
                == "running"
            )
            conn.execute(
                "UPDATE crawl_runs SET pipeline_status='completed' WHERE run_id=%s",
                (managed,),
            )
            try:
                rerun.main()
            except RuntimeError:
                pass
            else:
                raise AssertionError("Closed VPN rerun was accepted")
    print(
        "PASS: exact HTML run; parser scope; per-run links; rerun by ward; verified VPN rerun reuses preflight run; ward limit; closed context rejected"
    )
    conn.close()
finally:
    os.environ["POSTGRES_DB"] = original_db
    admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(qa)))
    admin.close()
