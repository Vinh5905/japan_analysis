from __future__ import annotations

import argparse
import json
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
    links_file = Path(args.links_file)
    report_dir = Path(args.report_dir)
    repository = CrawlerMetadataRepository.from_env()
    try:
        failed_tasks = repository.fetch_failed_crawl_tasks(
            source_id=args.source_id,
            limit=args.limit,
        )
        deduped_tasks, task_groups = dedupe_failed_tasks(failed_tasks)
        if not deduped_tasks:
            print("No failed crawl_tasks found for manual rerun.")
            return 0

        write_links_file(links_file=links_file, failed_tasks=deduped_tasks)
        print(
        f"Selected {len(failed_tasks)} latest failed task rows "
            f"as {len(deduped_tasks)} unique URLs.",
        )
        print(f"Wrote manual suumo_html links to {links_file}")

        if args.dry_run:
            report = build_report(
                manual_run_id=None,
                source_id=args.source_id,
                selected_tasks=deduped_tasks,
                task_groups=task_groups,
                rerun_results=[],
                scrapy_exit_code=None,
                dry_run=True,
            )
            json_path, ids_path = write_report(report_dir=report_dir, report=report)
            print(f"Dry run report: {json_path}")
            print(f"Dry run failed-id list: {ids_path}")
            return 0

        latest_run_id_before = repository.fetch_latest_run_id()
    finally:
        repository.close()

    scrapy_result = run_suumo_html(
        links_file=links_file,
        source_id=args.source_id,
        loglevel=args.loglevel,
    )

    repository = CrawlerMetadataRepository.from_env()
    try:
        manual_run_ids = repository.fetch_manual_run_ids_after(
            run_id=latest_run_id_before,
            source_id=args.source_id,
        )
        if not manual_run_ids:
            raise RuntimeError("suumo_html did not create a manual crawl_run")

        manual_run_id = manual_run_ids[-1]
        rerun_results = repository.fetch_task_results_for_run(manual_run_id)
        report = build_report(
            manual_run_id=manual_run_id,
            source_id=args.source_id,
            selected_tasks=deduped_tasks,
            task_groups=task_groups,
            rerun_results=rerun_results,
            scrapy_exit_code=scrapy_result.returncode,
            dry_run=False,
        )
        json_path, ids_path = write_report(report_dir=report_dir, report=report)
        print(f"Manual rerun crawl_run: {manual_run_id}")
        print(f"Failed again original task ids: {report['failed_again_original_task_ids']}")
        print(f"Failed-again report: {json_path}")
        print(f"Failed-again id list: {ids_path}")
    finally:
        repository.close()
        if not args.keep_links_file and links_file.exists():
            links_file.unlink()

    return scrapy_result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
