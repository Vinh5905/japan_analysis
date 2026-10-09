from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.metadata_db import (  # noqa: E402
    CrawlTaskResult,
    CrawlerMetadataRepository,
    FailedCrawlTask,
)


LINKS_FILE = Path("tmp/manual_failed_suumo_html_links.txt")
REPORT_DIR = Path("tmp/manual_rerun_reports")
SOURCE_ID = 1


def parse_args() -> argparse.Namespace:
    """Parse manual rerun options."""

    parser = argparse.ArgumentParser(
        description=(
            "Select URL hashes whose latest crawl_task is failed, rerun them "
            "through suumo_html, and write the ids that failed again."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum failed crawl_tasks rows to select. Default 0 means all.",
    )
    parser.add_argument(
        "--source-id",
        type=int,
        default=SOURCE_ID,
        help="crawl_sources.source_id to rerun. Default is 1 for SUUMO.",
    )
    parser.add_argument(
        "--links-file",
        default=str(LINKS_FILE),
        help="Temporary links file passed to suumo_html.",
    )
    parser.add_argument(
        "--report-dir",
        default=str(REPORT_DIR),
        help="Directory where failed-again reports are written.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print/write selected failed tasks; do not run suumo_html.",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        help="Scrapy LOG_LEVEL override for suumo_html.",
    )
    parser.add_argument(
        "--keep-links-file",
        action="store_true",
        help="Keep the temporary links file after a successful script run.",
    )
    return parser.parse_args()


def absolute_task_url(task: FailedCrawlTask) -> str:
    """Return an absolute URL suitable for Scrapy from crawl_tasks.url."""

    if task.url.startswith("http://") or task.url.startswith("https://"):
        return task.url
    if task.url.startswith("//"):
        return f"https:{task.url}"
    if task.url.startswith("/"):
        return f"{task.base_url.rstrip('/')}{task.url}"

    return f"{task.base_url.rstrip('/')}/{task.url}"


def dedupe_failed_tasks(
    failed_tasks: list[FailedCrawlTask],
) -> tuple[list[FailedCrawlTask], dict[str, list[FailedCrawlTask]]]:
    """Keep one URL per url_hash while preserving every original failed task id."""

    task_groups: dict[str, list[FailedCrawlTask]] = {}
    deduped_tasks: list[FailedCrawlTask] = []
    for task in failed_tasks:
        if task.url_hash not in task_groups:
            task_groups[task.url_hash] = []
            deduped_tasks.append(task)

        task_groups[task.url_hash].append(task)

    return deduped_tasks, task_groups


def write_links_file(links_file: Path, failed_tasks: list[FailedCrawlTask]) -> None:
    """Write absolute URLs for suumo_html to rerun."""

    links_file.parent.mkdir(parents=True, exist_ok=True)
    urls = [absolute_task_url(task) for task in failed_tasks]
    links_file.write_text("\n".join(urls) + "\n", encoding="utf-8")


def run_suumo_html(
    links_file: Path,
    source_id: int,
    loglevel: str,
    run_id: int | None = None,
    area_label: str = "",
) -> subprocess.CompletedProcess[str]:
    """Run suumo_html against the generated manual links file."""

    command = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "suumo_html",
        "-s",
        f"SUUMO_HTML_LINKS_FILE={links_file}",
        "-s",
        "SUUMO_RUN_CREATED_BY=manual",
        "-s",
        f"SUUMO_SOURCE_ID={source_id}",
        "-s",
        "SUUMO_HTML_LINK_LIMIT=0",
        "-s",
        f"LOG_LEVEL={loglevel}",
    ]
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        env={**os.environ, "SUUMO_RUN_ID": str(run_id), "TELEGRAM_PIPELINE_RUN_ID": str(run_id), "SUUMO_RUN_AREA": area_label} if run_id else dict(os.environ),
    )


def build_report(
    manual_run_id: int | None,
    source_id: int,
    selected_tasks: list[FailedCrawlTask],
    task_groups: dict[str, list[FailedCrawlTask]],
    rerun_results: list[CrawlTaskResult],
    scrapy_exit_code: int | None,
    dry_run: bool,
) -> dict[str, object]:
    """Build a JSON report of original ids that failed again."""

    failed_results = [result for result in rerun_results if result.status == "failed"]
    failed_again_entries = []
    failed_again_original_task_ids: list[int] = []
    for result in failed_results:
        original_tasks = task_groups.get(result.url_hash, [])
        original_task_ids = [task.task_id for task in original_tasks]
        failed_again_original_task_ids.extend(original_task_ids)
        failed_again_entries.append(
            {
                "original_task_ids": original_task_ids,
                "rerun_task_id": result.task_id,
                "url": result.url,
                "url_hash": result.url_hash,
                "status": result.status,
                "error_type": result.error_type,
                "error_message": result.error_message,
            }
        )

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "source_id": source_id,
        "manual_run_id": manual_run_id,
        "scrapy_exit_code": scrapy_exit_code,
        "selected_failed_task_count": sum(len(tasks) for tasks in task_groups.values()),
        "unique_url_count": len(selected_tasks),
        "rerun_task_count": len(rerun_results),
        "failed_again_count": len(failed_again_entries),
        "failed_again_original_task_ids": sorted(failed_again_original_task_ids),
        "failed_again_rerun_task_ids": [result.task_id for result in failed_results],
        "failed_again": failed_again_entries,
    }


def write_report(report_dir: Path, report: dict[str, object]) -> tuple[Path, Path]:
    """Write JSON report and a plain id list for manual inspection."""

    report_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    json_path = report_dir / f"manual_rerun_failed_{timestamp}.json"
    ids_path = report_dir / f"manual_rerun_failed_task_ids_{timestamp}.txt"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    failed_ids = report["failed_again_original_task_ids"]
    ids_path.write_text(
        "\n".join(str(task_id) for task_id in failed_ids) + ("\n" if failed_ids else ""),
        encoding="utf-8",
    )
    return json_path, ids_path


def main() -> int:
    """Run manual failed-task HTML reruns and write failed-again reports."""

    args = parse_args()
    repository = CrawlerMetadataRepository.from_env()
    exit_code = 0
    try:
        context_run, context_area = None, None
        required = os.environ.get('SUUMO_REQUIRE_VPN_CONTEXT', '').lower() in {'true','1','yes'}
        if required and not args.dry_run:
            rid, vid = os.environ.get('SUUMO_RUN_ID',''), os.environ.get('SUUMO_VPN_ID','')
            if not rid.isdigit() or not vid.isdigit():
                raise RuntimeError('Use the host runner --rerun-failed-html --area-id; verified VPN context required')
            with repository.connection.cursor() as cursor:
                cursor.execute("""SELECT r.run_id,r.area_id FROM crawl_runs r JOIN crawl_vpn_attempts a
                  ON a.run_id=r.run_id AND a.vpn_id=r.vpn_id WHERE r.run_id=%s AND r.vpn_id=%s
                  AND r.source_id=%s AND r.pipeline_status='running' AND a.status='success'
                  AND r.cleanup_confirmed_at IS NULL AND r.finished_at IS NULL
                  AND r.area_id IS NOT NULL""",(int(rid),int(vid),args.source_id))
                context = cursor.fetchone()
            if not context:
                raise RuntimeError('Rerun VPN context is invalid or closed')
            context_run, context_area = context
        tasks = repository.fetch_failed_crawl_tasks(source_id=args.source_id, limit=args.limit, area_id=context_area)
        groups = {}
        # Group by the original run's stable ward identity, never infer from URL.
        with repository.connection.cursor() as cursor:
            cursor.execute("SELECT run_id,area_id,area_snapshot FROM crawl_runs WHERE run_id=ANY(%s)", ([t.run_id for t in tasks],))
            scopes = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        for task in tasks:
            area_id, snapshot = scopes[task.run_id]
            if area_id is None:
                raise RuntimeError("Failed task has no ward; apply the confirmed legacy backfill first")
            if context_area is not None and area_id != context_area:
                continue
            groups.setdefault(area_id, []).append(task)
        if not groups:
            print("No failed crawl_tasks found for manual rerun.")
        for area_id, failed_tasks in groups.items():
            selected, task_groups = dedupe_failed_tasks(failed_tasks)
            links_file = Path(args.links_file).with_name(f"area_{area_id}_{__import__('uuid').uuid4().hex}_" + Path(args.links_file).name)
            write_links_file(links_file, selected)
            manual_run_id, code, results = None, None, []
            if not args.dry_run:
                # This tool reruns HTML only, so it has no host pipeline key.
                # Reserve the exact run instead of racing MAX(run_id).
                with repository.connection.cursor() as cursor:
                    if context_run is not None:
                        manual_run_id = context_run
                    else:
                        cursor.execute("""INSERT INTO crawl_runs(source_id,area_id,area_snapshot,created_by,pipeline_status)
                          SELECT source_id,area_id,jsonb_build_object('area_id',area_id,'prefecture',prefecture,
                           'district',district,'municipality',municipality,'ward',ward,'display_name',display_name,'sc',sc),
                           'manual','running' FROM crawl_areas WHERE area_id=%s AND source_id=%s RETURNING run_id""", (area_id,args.source_id))
                        manual_run_id = cursor.fetchone()[0]
                snapshot = scopes[failed_tasks[0].run_id][1] or {}
                label = " · ".join(str(snapshot[k]) for k in ("prefecture","district","municipality","ward") if snapshot.get(k))
                result = run_suumo_html(links_file,args.source_id,args.loglevel,manual_run_id,label)
                code = result.returncode
                exit_code = exit_code or code
                results = repository.fetch_task_results_for_run(manual_run_id)
                if context_run is None:
                    with repository.connection.cursor() as cursor:
                        cursor.execute("UPDATE crawl_runs SET pipeline_status=NULL WHERE run_id=%s", (manual_run_id,))
            report = build_report(manual_run_id,args.source_id,selected,task_groups,results,code,args.dry_run)
            report['area_id'] = area_id
            json_path, ids_path = write_report(Path(args.report_dir), report)
            print(f"Ward {area_id}; HTML run {manual_run_id}; report {json_path}; IDs {ids_path}")
            if not args.keep_links_file:
                links_file.unlink(missing_ok=True)
    finally:
        repository.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
