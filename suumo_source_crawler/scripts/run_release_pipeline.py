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
from pathlib import Path
from typing import Mapping, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
CRAWLER_ROOT = PROJECT_ROOT / "crawler"
sys.path.insert(0, str(CRAWLER_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.runtime_lock import release_lock  # noqa: E402
from scripts.telegram_state import state_for, install_context  # noqa: E402

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
    parser.add_argument("--area-id", type=int, help="Ward ID for direct manual pipeline")
    parser.add_argument('--rerun-failed-html', action='store_true', help='Rerun failed HTML for --area-id, using normal VPN lifecycle')
    parser.add_argument('--limit', dest='rerun_limit', type=int, default=0, help='Maximum failed tasks for HTML rerun')
    parser.add_argument("--vpn-service", default="openvpn-client@japan")
    parser.add_argument("--vpn-interface", default="tun0")
    parser.add_argument("--vpn-managed-by-systemd", action="store_true",
                        help="Only for the unit that supplies ExecStartPre and ExecStopPost VPN hooks.")
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
        "URL đã xử lý": int(html.get("html_success_count", 0)) + int(html.get("html_failed_count", 0)),
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
    secrets: tuple[str, ...] = (),
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
        secrets=secrets,
    )


def main() -> int:
    """Hold the release lock while running all pipeline commands."""

    args = parse_args()
    try:
        with release_lock(args.compose_file.resolve().parent):
            if args.vpn_managed_by_systemd:
                return run_pipeline(args)
            return run_with_vpn(args)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 75


def run_with_vpn(args: argparse.Namespace) -> int:
    """For manual runs, verify VPN before crawling and confirm shutdown even on failure."""
    from scripts.telegram_control import Host
    from scripts.area_catalog import refresh, ward_url
    from scripts.crawl_dispatcher import choose_area
    state = state_for(args.env_file)
    host = Host(args.env_file, args.compose_file, read_env_file(args.env_file))
    if host.busy() or host.unresolved():
        raise RuntimeError("Existing pipeline/cleanup must finish before a manual launch")
    refresh(host)
    areas = host.areas()
    area_id = getattr(args, "area_id", None)
    if getattr(args, 'rerun_failed_html', False) and not area_id:
        raise ValueError('Managed HTML rerun requires --area-id; one ward per VPN run')
    area = next((a for a in areas if a["area_id"] == area_id), None) if area_id else choose_area(areas)
    if not area:
        raise ValueError("Unknown area_id")
    area["search_url"] = ward_url(host.values.get("SUUMO_SEARCH_URL", ""), area["sc"])
    state.launch(area, "manual")
    scripts = PROJECT_ROOT / "scripts"
    common = ["--env-file", str(args.env_file.resolve()), "--service", args.vpn_service,
              "--interface", args.vpn_interface]
    environment = dict(os.environ)
    environment["SUUMO_RUN_CREATED_BY"] = "manual"
    directory = args.compose_file.resolve().parent
    result_code = 1
    try:
        preflight = run_command([sys.executable, str(scripts / "ensure_openvpn.py"), *common], directory, environment)
        result_code = preflight.return_code
        if result_code == 0:
            result_code = run_pipeline(args)
    except BaseException:
        # Cleanup also runs on Ctrl-C or an unexpected Python exception.
        result_code = 1
        raise
    finally:
        environment["SERVICE_RESULT"] = "success" if result_code == 0 else "exit-code"
        cleanup = run_command([sys.executable, str(scripts / "stop_openvpn.py"), *common,
                               "--compose-file", str(args.compose_file.resolve()), "--lock-held"], directory, environment)
        if cleanup.return_code != 0:
            print("Pipeline ended but VPN shutdown was NOT confirmed", file=sys.stderr, flush=True)
            result_code = result_code or cleanup.return_code
    return result_code


def run_pipeline(args: argparse.Namespace) -> int:
    """Run infrastructure bootstrap and all crawler jobs in fail-fast order."""

    compose_file = args.compose_file.resolve()
    env_file = args.env_file.resolve()

    try:
        dotenv_values = read_env_file(env_file)
    except (OSError, UnicodeError) as exc:
        print(f"Cannot read release environment: {exc}", file=sys.stderr)
        return 2

    host_environment = merged_environment(dotenv_values)
    hostname = socket.gethostname()
    state = state_for(env_file)
    run = state.get("pipeline")
    if not run or run.get("status") != "running" or run.get("step") != "vpn_ready" or not run.get('vpn', {}).get('vpn_id'):
        print("VPN preflight context is missing or failed; refusing crawl", file=sys.stderr)
        return 2
    run_id = run["run_id"]
    install_context(run)
    for name in ("SUUMO_RUN_ID", "SUUMO_RUN_AREA", "SUUMO_SEARCH_URL", "SUUMO_HTML_LINKS_FILE", "SUUMO_VPN_ID", "SUUMO_VPN_FILENAME"):
        host_environment[name] = os.environ[name]
    host_environment["SUUMO_RUN_CREATED_BY"] = run["source"]
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
    rerun = getattr(args, 'rerun_failed_html', False)
    for service_name in (("suumo-html", "suumo-page") if rerun else ("suumo-links", "suumo-html", "suumo-page")):
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
                    "-e",
                    f"SUUMO_RUN_CREATED_BY={run['source']}",
                    "-e", f"SUUMO_RUN_ID={run_id}",
                    "-e", f"SUUMO_RUN_AREA={host_environment['SUUMO_RUN_AREA']}",
                    "-e", f"SUUMO_SEARCH_URL={run['area']['search_url']}",
                    "-e", f"SUUMO_HTML_LINKS_FILE={host_environment['SUUMO_HTML_LINKS_FILE']}",
                    "-e", f"SUUMO_VPN_ID={host_environment['SUUMO_VPN_ID']}",
                    "-e", f"SUUMO_VPN_FILENAME={host_environment['SUUMO_VPN_FILENAME']}",
                    *(["suumo-tools", "manual-rerun-failed-html", "--limit", str(getattr(args, 'rerun_limit', 0))]
                      if rerun and service_name == 'suumo-html' else [service_name]),
                ],
            )
        )

    tmp_directory = resolve_tmp_directory(compose_file, dotenv_values)
    run_directory = tmp_directory / "telegram" / run_id

    try:
        for step_name, command in commands:
            state.progress(step_name)
            print(f"Starting pipeline step: {step_name}", flush=True)
            result = run_command(command, compose_file.parent, host_environment)
            # Scrapy can exit zero after a fatal accounting close; do not continue.
            summaries = read_spider_summaries(run_directory)
            fatal = (run_directory / 'vpn_accounting_failed').exists() or any(
                s.get('status') == 'failed' or s.get('close_reason') == 'vpn_accounting_failed'
                for s in summaries.values())
            # No summary can mean a zero-exit Scrapy startup failure or unwritable tmp.
            # An empty HTML rerun legitimately launches no spider, so allow that case.
            spider_name = step_name.replace('-', '_')
            if spider_name in SPIDER_NAMES and spider_name not in summaries and not (rerun and step_name == 'suumo-html'):
                fatal = True
            if result.return_code != 0 or fatal:
                state.progress(step_name, status="failed")
                duration_seconds = max(0.0, time.monotonic() - started_monotonic)
                notifier.send_message(
                    pipeline_failed_message(
                        step_name=step_name,
                        result=result,
                        started_at=started_at,
                        duration_seconds=duration_seconds,
                        hostname=hostname,
                        secrets=notifier.config.secrets,
                    )
                )
                return result.return_code or 1

        summaries = read_spider_summaries(run_directory)
        # The cleanup hook publishes completion only after the VPN has closed.
        state.progress("awaiting_vpn_cleanup", completion={"summaries": summaries, "started_at": started_at, "hostname": hostname})
        return 0
    finally:
        if run_directory.is_dir():
            shutil.rmtree(run_directory, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
