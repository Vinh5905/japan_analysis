#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
CRAWLER_ROOT = PROJECT_ROOT / "crawler"
sys.path.insert(0, str(CRAWLER_ROOT))

from crawler.telegram_notifier import (  # noqa: E402
    TelegramNotifier,
    build_event_message,
    current_timestamp,
    infer_possible_causes,
    sanitize_text,
)


PIPELINE_NAME = "suumo_crawler_pipeline"
SPIDER_NAMES = ("suumo_links", "suumo_html", "suumo_page")


@dataclass(frozen=True)
class CommandResult:
    """Store one streamed subprocess result and its diagnostic tail."""

    return_code: int
    output_tail: str
    error_type: str | None = None
    error_message: str | None = None


def parse_args() -> argparse.Namespace:
    """Parse paths needed by the host-side release pipeline runner."""

    parser = argparse.ArgumentParser(
        description="Run the release crawler pipeline and publish Telegram lifecycle events.",
    )
    parser.add_argument(
        "--compose-file",
        type=Path,
        default=REPOSITORY_ROOT / "docker-compose.release.yml",
        help="Path to docker-compose.release.yml.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPOSITORY_ROOT / ".env",
        help="Path to the release .env file.",
    )
    return parser.parse_args()


def read_env_file(path: Path) -> dict[str, str]:
    """Read simple dotenv assignments needed by the runner without extra packages."""

    if not path.is_file():
        raise FileNotFoundError(f"Environment file does not exist: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def merged_environment(dotenv_values: Mapping[str, str]) -> dict[str, str]:
    """Let explicit host environment values override the release dotenv file."""

    merged = dict(dotenv_values)
    merged.update(os.environ)
    return merged


def run_command(
    command: Sequence[str],
    working_directory: Path,
    environ: Mapping[str, str],
) -> CommandResult:
    """Stream a command to journald/terminal while retaining a short failure tail."""

    output_tail: deque[str] = deque(maxlen=40)
    try:
        process = subprocess.Popen(
            list(command),
            cwd=working_directory,
            env=dict(environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        return CommandResult(
            return_code=127,
            output_tail="",
            error_type=type(exc).__name__,
            error_message=sanitize_text(exc),
        )

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        output_tail.append(line.rstrip())

    return_code = process.wait()
    return CommandResult(
        return_code=return_code,
        output_tail="\n".join(output_tail),
    )


def resolve_tmp_directory(
    compose_file: Path,
    dotenv_values: Mapping[str, str],
) -> Path:
    """Resolve the host directory mounted to /app/crawler/tmp by release Compose."""

    configured_path = Path(dotenv_values.get("CRAWLER_TMP_DIR", "./tmp"))
    if configured_path.is_absolute():
        return configured_path
    return (compose_file.parent / configured_path).resolve()


def read_spider_summaries(run_directory: Path) -> dict[str, dict[str, object]]:
    """Read summaries written by the three one-shot Scrapy containers."""

    summaries: dict[str, dict[str, object]] = {}
    for spider_name in SPIDER_NAMES:
        summary_path = run_directory / f"{spider_name}.json"
        if not summary_path.is_file():
            continue
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"Could not read summary {summary_path}: {exc}", file=sys.stderr)
            continue
        if isinstance(payload, dict):
            summaries[spider_name] = payload
    return summaries


def pipeline_completed_message(
    summaries: Mapping[str, Mapping[str, object]],
    started_at: str,
    duration_seconds: float,
    hostname: str,
) -> str:
    """Build the final aggregate pipeline message from per-spider summaries."""

    links = summaries.get("suumo_links", {})
    html = summaries.get("suumo_html", {})
    page = summaries.get("suumo_page", {})
    warnings = [
        str(summary.get("warning_message"))
        for summary in summaries.values()
        if summary.get("warning_message")
    ]
    if len(summaries) != len(SPIDER_NAMES):
        warnings.append(
            "Không đọc được đủ summary của ba spider; kiểm tra image release và tmp volume."
        )
    fields: dict[str, object] = {
        "Pipeline": PIPELINE_NAME,
        "Host": hostname,
        "Bắt đầu": started_at,
        "Kết thúc": current_timestamp(),
        "Thời gian chạy": f"{duration_seconds:.2f} giây",
        "Các bước hoàn thành": f"{len(summaries)}/{len(SPIDER_NAMES)}",
        "URL mới": links.get("new_links", 0),
        "HTML thành công": html.get("html_success_count", 0),
        "HTML thất bại": html.get("html_failed_count", 0),
        "Records đã parse": page.get("parsed_record_count", 0),
        "Records valid": page.get("valid_record_count", 0),
        "Records invalid": page.get("invalid_record_count", 0),
        "Batches": page.get("batch_count", 0),
    }
    if warnings:
        fields["Cảnh báo"] = " | ".join(warnings)
    title = "PIPELINE HOÀN THÀNH CÓ CẢNH BÁO" if warnings else "PIPELINE HOÀN THÀNH"
    return build_event_message(title, fields)


def pipeline_failed_message(
    step_name: str,
    result: CommandResult,
    started_at: str,
    duration_seconds: float,
    hostname: str,
) -> str:
    """Build a required failure message with exception context and likely causes."""

    error_type = result.error_type or "CommandFailed"
    error_message = result.error_message or result.output_tail or (
        f"Lệnh của bước {step_name} kết thúc với exit code {result.return_code}"
    )
    return build_event_message(
        "PIPELINE THẤT BẠI",
        {
            "Pipeline": PIPELINE_NAME,
            "Bước lỗi": step_name,
            "Exception type": error_type,
            "Error message": error_message,
            "Exit code": result.return_code,
            "Host": hostname,
            "Bắt đầu": started_at,
            "Thất bại lúc": current_timestamp(),
            "Thời gian chạy": f"{duration_seconds:.2f} giây",
        },
        possible_causes=infer_possible_causes(error_message),
    )


def main() -> int:
    """Run infrastructure bootstrap and all crawler jobs in fail-fast order."""

    args = parse_args()
    compose_file = args.compose_file.resolve()
    env_file = args.env_file.resolve()

    try:
        dotenv_values = read_env_file(env_file)
    except (OSError, UnicodeError) as exc:
        print(f"Cannot read release environment: {exc}", file=sys.stderr)
        return 2

    host_environment = merged_environment(dotenv_values)
    hostname = socket.gethostname()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    host_environment["TELEGRAM_HOSTNAME"] = hostname
    host_environment["TELEGRAM_PIPELINE_RUN_ID"] = run_id

    notifier = TelegramNotifier.from_env(host_environment)
    started_at = current_timestamp(host_environment)
    started_monotonic = time.monotonic()
    notifier.send_message(
        build_event_message(
            "PIPELINE BẮT ĐẦU",
            {
                "Pipeline": PIPELINE_NAME,
                "Host": hostname,
                "Thời gian": started_at,
            },
        )
    )

    compose_base = [
        "docker",
        "compose",
        "--env-file",
        str(env_file),
        "-f",
        str(compose_file),
    ]
    commands: list[tuple[str, list[str]]] = [
        (
            "start_postgres_minio",
            [*compose_base, "up", "-d", "--pull", "never", "postgres", "minio"],
        ),
        (
            "crawler_init",
            [*compose_base, "run", "--rm", "--pull", "never", "crawler-init"],
        ),
    ]
    for service_name in ("suumo-links", "suumo-html", "suumo-page"):
        commands.append(
            (
                service_name,
                [
                    *compose_base,
                    "run",
                    "--rm",
                    "--pull",
                    "never",
                    "-e",
                    f"TELEGRAM_HOSTNAME={hostname}",
                    "-e",
                    f"TELEGRAM_PIPELINE_RUN_ID={run_id}",
                    service_name,
                ],
            )
        )

    tmp_directory = resolve_tmp_directory(compose_file, dotenv_values)
    run_directory = tmp_directory / "telegram" / run_id

    try:
        for step_name, command in commands:
            print(f"Starting pipeline step: {step_name}", flush=True)
            result = run_command(command, compose_file.parent, host_environment)
            if result.return_code != 0:
                duration_seconds = max(0.0, time.monotonic() - started_monotonic)
                notifier.send_message(
                    pipeline_failed_message(
                        step_name=step_name,
                        result=result,
                        started_at=started_at,
                        duration_seconds=duration_seconds,
                        hostname=hostname,
                    )
                )
                return result.return_code or 1

        summaries = read_spider_summaries(run_directory)
        duration_seconds = max(0.0, time.monotonic() - started_monotonic)
        notifier.send_message(
            pipeline_completed_message(
                summaries=summaries,
                started_at=started_at,
                duration_seconds=duration_seconds,
                hostname=hostname,
            )
        )
        return 0
    finally:
        if run_directory.is_dir():
            shutil.rmtree(run_directory, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
