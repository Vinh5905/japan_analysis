#!/usr/bin/env python3
"""Stop leftover crawler tasks, then stop and verify the host OpenVPN tunnel."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import time
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "crawler"))

from crawler.telegram_notifier import TelegramNotifier, build_event_message  # noqa: E402
from scripts.run_release_pipeline import read_env_file, pipeline_completed_message  # noqa: E402
from scripts.runtime_lock import release_lock  # noqa: E402
from scripts.telegram_state import state_for, install_context  # noqa: E402


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess]
PIPELINE_SERVICES = {"crawler-init", "suumo-links", "suumo-html", "suumo-page", "suumo-rerun-html"}


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess:
    """Bound each host command so a hung command cannot block cleanup forever."""
    environment = dict(os.environ)
    environment.pop("SUUMO_CRAWLER_TAG", None)
    return subprocess.run(list(command), check=False, capture_output=True, text=True,
                          timeout=30, env=environment)


def vpn_stopped_reason(service: str, interface: str, runner: CommandRunner = run_command) -> tuple[bool, str]:
    """Require no OpenVPN process, no UP tunnel and no remaining tunnel routes."""
    state = runner(("systemctl", "show", service, "--property=ActiveState,MainPID"))
    if state.returncode != 0:
        return False, "cannot read OpenVPN service state"
    values = dict(line.split("=", 1) for line in state.stdout.splitlines() if "=" in line)
    if values.get("ActiveState") not in {"inactive", "failed"} or values.get("MainPID") != "0":
        return False, f"service is {values.get('ActiveState', 'unknown')}, MainPID={values.get('MainPID', 'unknown')}"
    links = runner(("ip", "-j", "link", "show"))
    if links.returncode != 0:
        return False, "cannot inspect network interfaces"
    for link in json.loads(links.stdout):
        if link.get("ifname") == interface and "UP" in link.get("flags", []):
            return False, f"interface {interface} is still UP"
    for family in ("-4", "-6"):
        routes = runner(("ip", "-j", family, "route", "show", "table", "all"))
        if routes.returncode != 0:
            return False, f"cannot inspect {family} routes"
        if any(route.get("dev") == interface for route in json.loads(routes.stdout)):
            return False, f"{family} routes still use {interface}"
    return True, f"{service} is stopped, {interface} is absent/down and tunnel routes are gone"


def stop_vpn(service: str, interface: str, stop_attempts: int = 3, checks_per_attempt: int = 30,
             required_consecutive_checks: int = 3, check_interval_seconds: float = 2,
             runner: CommandRunner = run_command, sleeper: Callable[[float], None] = time.sleep,
             notifier: TelegramNotifier | None = None) -> bool:
    """Request a stop with retries and accept only consecutively verified shutdown."""
    if notifier is not None:
        notifier.send_message(build_event_message("ĐANG TẮT VPN", {"Service": service, "Host": socket.gethostname()}))
    reason = "shutdown has not been confirmed"
    try:
        for attempt in range(1, stop_attempts + 1):
            result = runner(("systemctl", "stop", "--no-block", service))
            if result.returncode != 0:
                print(f"VPN stop request {attempt}/{stop_attempts} failed", file=sys.stderr, flush=True)
            consecutive = 0
            for check in range(1, checks_per_attempt + 1):
                stopped, reason = vpn_stopped_reason(service, interface, runner)
                consecutive = consecutive + 1 if stopped else 0
                print(f"VPN shutdown {attempt}/{stop_attempts}, check {check}/{checks_per_attempt}: {reason}", flush=True)
                if consecutive >= required_consecutive_checks:
                    if notifier is not None:
                        notifier.send_message(build_event_message("VPN ĐÃ TẮT — ĐÃ XÁC NHẬN", {
                            "Service": service, "Trạng thái": reason,
                            "Kết quả chạy trước cleanup": os.environ.get("SERVICE_RESULT", "manual"),
                        }))
                    return True
                if check < checks_per_attempt:
                    sleeper(check_interval_seconds)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        # Failure to inspect host state is never interpreted as a closed VPN.
        reason = f"{type(exc).__name__}: {exc}"
    print(f"VPN shutdown NOT confirmed: {reason}", file=sys.stderr, flush=True)
    if notifier is not None:
        notifier.send_message(build_event_message("KHÔNG XÁC NHẬN ĐƯỢC VPN ĐÃ TẮT", {
            "Service": service, "Lý do": reason, "Kết quả": "cleanup failed; kiểm tra VPS",
        }))
    return False


def remaining_crawlers(project: str, runner: CommandRunner) -> list[str]:
    """List only this Compose project's running pipeline containers."""
    result = runner(("docker", "ps", "--filter", f"label=com.docker.compose.project={project}",
                     "--format", '{{.ID}} {{.Label "com.docker.compose.service"}}'))
    if result.returncode != 0:
        raise RuntimeError("Cannot inspect remaining crawler containers; keeping VPN on")
    return [parts[0] for line in result.stdout.splitlines()
            if len(parts := line.split()) == 2 and parts[1] in PIPELINE_SERVICES]


def finish_crawler_containers(compose_file: Path, env_file: Path, runner: CommandRunner = run_command) -> None:
    """After interruption, stop lingering tasks before they can lose their VPN route."""
    config = runner(("docker", "compose", "--env-file", str(env_file), "-f", str(compose_file),
                     "config", "--format", "json"))
    if config.returncode != 0:
        raise RuntimeError("Cannot resolve crawler Compose project; keeping VPN on")
    # Compose config contains credentials; only extract its name, never print the output.
    project = json.loads(config.stdout)["name"]
    containers = remaining_crawlers(project, runner)
    if containers:
        print(f"Stopping {len(containers)} unfinished crawler container(s) before VPN shutdown", flush=True)
        result = runner(("docker", "stop", "--time", "10", *containers))
        if result.returncode != 0:
            raise RuntimeError("Cannot stop remaining crawler containers; keeping VPN on")
    if remaining_crawlers(project, runner):
        raise RuntimeError("Crawler containers are still running; keeping VPN on")


def parse_args() -> argparse.Namespace:
    """Parse the cleanup bounds and paths passed by systemd or the manual runner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=REPOSITORY_ROOT / ".env")
    parser.add_argument("--compose-file", type=Path, default=REPOSITORY_ROOT / "docker-compose.release.yml")
    parser.add_argument("--service", default="openvpn-client@japan")
    parser.add_argument("--interface", default="tun0")
    parser.add_argument("--stop-attempts", type=int, default=3)
    parser.add_argument("--checks-per-attempt", type=int, default=30)
    parser.add_argument("--required-consecutive-checks", type=int, default=3)
    parser.add_argument("--check-interval-seconds", type=float, default=2)
    parser.add_argument("--lock-held", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if min(args.stop_attempts, args.checks_per_attempt, args.required_consecutive_checks) < 1:
        parser.error("attempts and check counts must be positive")
    if args.required_consecutive_checks > args.checks_per_attempt or not 0 <= args.check_interval_seconds < float("inf"):
        parser.error("invalid consecutive-check count or interval")
    return args


def main() -> int:
    """Confirm all tasks ended and the VPN closed, returning failure if either cannot be verified."""
    args = parse_args()
    try:
        values = read_env_file(args.env_file)
    except (OSError, UnicodeError) as exc:
        print(f"Cannot read Telegram environment: {exc}; still attempting cleanup", file=sys.stderr)
        values = {}
    values.update(os.environ)
    notifier = TelegramNotifier.from_env(values)
    state, run = None, {}
    try:
        state = state_for(args.env_file)
        previous = state.get("pipeline", {})
        if previous.get("status") == "launching" and previous.get("pipeline_key"):
            from scripts.telegram_control import Host
            existing = Host(args.env_file.resolve(), args.compose_file.resolve(), read_env_file(args.env_file)).pipeline_by_key(previous["pipeline_key"])
            if existing and not existing.get("cleanup_confirmed_at"):
                previous = state.progress("vpn_preflight_failed", run_id=str(existing["run_id"]), status="failed")
        if previous.get("run_id") and previous.get("status") != "completed":
            if previous.get("step") in {"vpn_preflight", "vpn_preflight_failed"}:
                state.progress("vpn_preflight_failed", status="failed")
            run = state.progress("vpn_cleanup")
    except (OSError, sqlite3.Error, ValueError) as exc:
        # Durable status must never prevent mandatory VPN cleanup.
        print(f"Cannot read cleanup state: {type(exc).__name__}; still closing VPN", file=sys.stderr)
        state = None
    install_context(run)
    try:
        lock = nullcontext() if args.lock_held else release_lock(args.compose_file.resolve().parent)
        with lock:
            finish_crawler_containers(args.compose_file.resolve(), args.env_file.resolve())
            from scripts.docker_vpn import DockerVpn, docker_backend
            if docker_backend(values):
                from scripts.telegram_control import Host
                controller = DockerVpn(Host(args.env_file.resolve(), args.compose_file.resolve(), read_env_file(args.env_file)))
                notifier.send_message(build_event_message('ĐANG TẮT VPN', {'Service': 'Docker VPN'}))
                stopped = controller.stop() and vpn_stopped_reason(args.service, args.interface)[0]
                if stopped:
                    notifier.send_message(build_event_message('VPN ĐÃ TẮT — ĐÃ XÁC NHẬN', {'Service': 'Docker VPN', 'Trạng thái': 'crawler và container VPN đã dừng'}))
            else:
                stopped = stop_vpn(args.service, args.interface, args.stop_attempts, args.checks_per_attempt,
                                   args.required_consecutive_checks, args.check_interval_seconds, notifier=notifier)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"VPN cleanup failed: {exc}", file=sys.stderr, flush=True)
        notifier.send_message(build_event_message("VPN CLEANUP THẤT BẠI", {"Lý do": str(exc), "Kết quả": "chưa xác nhận VPN đã tắt"}))
        if state is not None:
            try:
                state.progress("vpn_cleanup_failed", status="failed", completion=None)
                from scripts.telegram_control import Host
                from scripts.crawl_dispatcher import persist_finish
                persist_finish(Host(args.env_file.resolve(), args.compose_file.resolve(), read_env_file(args.env_file)), state, False, False)
            except (OSError, sqlite3.Error, ValueError):
                print("Cannot persist failed cleanup state", file=sys.stderr)
        return 1
    service_result = os.environ.get("SERVICE_RESULT", "success")
    success = stopped and run.get("status") == "running" and service_result == "success" and bool(run.get("completion"))
    completion = run.get("completion")
    # Consume before sending, so a restarted hook cannot send completion twice.
    if state is not None and run:
        try:
            state.progress("completed" if success else "failed", status="completed" if success else "failed", completion=None)
        except (OSError, sqlite3.Error, ValueError):
            print("VPN cleanup ended, but cannot persist final status", file=sys.stderr)
            notifier.send_message(build_event_message("PIPELINE HOÀN THÀNH CÓ CẢNH BÁO", {
                "VPN": "đã xác nhận tắt" if stopped else "chưa xác nhận tắt", "Lưu trạng thái": "thất bại; kiểm tra journald"}))
            return 1
    if success:
        notifier.send_message(pipeline_completed_message(**completion, duration_seconds=max(0, time.time() - run["started"])) + "\n🔐 VPN: đã xác nhận tắt")
    elif run:
        notifier.send_message(build_event_message("PIPELINE THẤT BẠI", {
            "Lượt chạy": run.get("run_id", "chưa tạo"), "Kết quả service": service_result,
            "VPN": "đã xác nhận tắt" if stopped else "chưa xác nhận tắt", "Chi tiết": "Xem journald của pipeline."}))
    if state is not None and run:
        try:
            from scripts.telegram_control import Host
            from scripts.crawl_dispatcher import persist_finish, wake
            host = Host(args.env_file.resolve(), args.compose_file.resolve(), read_env_file(args.env_file))
            persist_finish(host, state, success, stopped)
            wake(host)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            print(f"Cleanup finalization failed: {type(exc).__name__}; dispatcher will block", file=sys.stderr)
            return 1
    return 0 if stopped else 1


if __name__ == "__main__":
    raise SystemExit(main())
