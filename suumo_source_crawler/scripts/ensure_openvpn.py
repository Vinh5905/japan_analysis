#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PROJECT_ROOT.parent
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "crawler"))

from crawler.telegram_notifier import (  # noqa: E402
    TelegramNotifier,
    build_event_message,
    machine_name,
)
from scripts.run_release_pipeline import read_env_file  # noqa: E402


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]
SleepFunction = Callable[[float], None]
VPN_ROUTES = ("0.0.0.0/1", "128.0.0.0/1")


def notify_vpn_event(
    notifier: TelegramNotifier | None,
    title: str,
    fields: dict[str, object],
    possible_causes: list[str] | None = None,
) -> None:
    """Send one best-effort VPN lifecycle event without blocking the pipeline."""

    if notifier is None:
        return
    notifier.send_message(
        build_event_message(
            title,
            fields,
            possible_causes=possible_causes,
        )
    )


def parse_args() -> argparse.Namespace:
    """Parse retry and health-check settings for the OpenVPN preflight."""

    parser = argparse.ArgumentParser(
        description="Ensure a host OpenVPN service is healthy before the crawler starts.",
    )
    parser.add_argument("--service", default="openvpn-client@japan")
    parser.add_argument("--interface", default="tun0")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=REPOSITORY_ROOT / ".env",
        help="Production dotenv file used for Telegram notifications.",
    )
    parser.add_argument("--restart-attempts", type=int, default=3)
    parser.add_argument("--checks-per-attempt", type=int, default=120)
    parser.add_argument("--required-consecutive-checks", type=int, default=3)
    parser.add_argument("--check-interval-seconds", type=float, default=2.0)
    args = parser.parse_args()

    for name in (
        "restart_attempts",
        "checks_per_attempt",
        "required_consecutive_checks",
    ):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be at least 1")
    if args.check_interval_seconds < 0:
        parser.error("--check-interval-seconds cannot be negative")
    if args.required_consecutive_checks > args.checks_per_attempt:
        parser.error("required consecutive checks cannot exceed checks per attempt")
    return args


def run_command(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """Run one host command and retain output for diagnostics."""

    return subprocess.run(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def command_succeeded(result: subprocess.CompletedProcess[str]) -> bool:
    """Return whether a subprocess completed successfully."""

    return result.returncode == 0


def service_state(
    service: str,
    runner: CommandRunner = run_command,
) -> str:
    """Return the current systemd active state for one service."""

    result = runner(("systemctl", "is-active", service))
    return result.stdout.strip() or result.stderr.strip() or "unknown"


def vpn_health_reason(
    service: str,
    interface: str,
    runner: CommandRunner = run_command,
) -> tuple[bool, str]:
    """Check systemd state, tunnel link, and both redirect-gateway routes."""

    state = service_state(service, runner=runner)
    if state != "active":
        return False, f"service state is {state}"

    link_result = runner(("ip", "-o", "link", "show", "dev", interface))
    if not command_succeeded(link_result) or "UP" not in link_result.stdout:
        return False, f"interface {interface} is not up"

    for network in VPN_ROUTES:
        route_result = runner(("ip", "-4", "route", "show", network))
        if not command_succeeded(route_result) or f"dev {interface}" not in route_result.stdout:
            return False, f"route {network} does not use {interface}"

    return True, f"{service} is active and redirect routes use {interface}"


def wait_for_stable_vpn(
    service: str,
    interface: str,
    checks_per_attempt: int,
    required_consecutive_checks: int,
    check_interval_seconds: float,
    runner: CommandRunner = run_command,
    sleeper: SleepFunction = time.sleep,
) -> bool:
    """Require several consecutive healthy checks before accepting the VPN."""

    consecutive_checks = 0
    for check_number in range(1, checks_per_attempt + 1):
        healthy, reason = vpn_health_reason(service, interface, runner=runner)
        if healthy:
            consecutive_checks += 1
            print(
                f"VPN health check {check_number}/{checks_per_attempt}: healthy "
                f"({consecutive_checks}/{required_consecutive_checks} consecutive)",
                flush=True,
            )
            if consecutive_checks >= required_consecutive_checks:
                return True
        else:
            consecutive_checks = 0
            print(
                f"VPN health check {check_number}/{checks_per_attempt}: unhealthy: {reason}",
                flush=True,
            )

        if check_number < checks_per_attempt:
            sleeper(check_interval_seconds)
    return False


def restart_vpn(
    service: str,
    runner: CommandRunner = run_command,
) -> bool:
    """Reset a stale failed state and request a non-blocking service restart."""

    runner(("systemctl", "reset-failed", service))
    restart_result = runner(("systemctl", "restart", "--no-block", service))
    if command_succeeded(restart_result):
        return True

    error_message = restart_result.stderr.strip() or restart_result.stdout.strip()
    print(f"Could not restart {service}: {error_message}", file=sys.stderr, flush=True)
    return False


def ensure_vpn(
    service: str,
    interface: str,
    restart_attempts: int,
    checks_per_attempt: int,
    required_consecutive_checks: int,
    check_interval_seconds: float,
    runner: CommandRunner = run_command,
    sleeper: SleepFunction = time.sleep,
    notifier: TelegramNotifier | None = None,
    hostname: str | None = None,
) -> bool:
    """Accept a healthy VPN or restart and verify it with bounded retries."""

    host = hostname or socket.gethostname()

    healthy, reason = vpn_health_reason(service, interface, runner=runner)
    if healthy:
        print(f"VPN preflight: {reason}; verifying stability", flush=True)
        notify_vpn_event(
            notifier,
            "VPN ĐANG ĐƯỢC KIỂM TRA",
            {
                "Trạng thái": "OpenVPN đang active; kiểm tra tunnel và route ổn định",
                "Service": service,
                "Interface": interface,
                "Host": host,
            },
        )
        if wait_for_stable_vpn(
            service,
            interface,
            checks_per_attempt=required_consecutive_checks,
            required_consecutive_checks=required_consecutive_checks,
            check_interval_seconds=check_interval_seconds,
            runner=runner,
            sleeper=sleeper,
        ):
            notify_vpn_event(
                notifier,
                "VPN ĐÃ BẬT",
                {
                    "Trạng thái": "active và tunnel ổn định",
                    "Service": service,
                    "Interface": interface,
                    "Host": host,
                    "Crawler": "được phép chạy",
                },
            )
            return True
        reason = "VPN đang active nhưng không duy trì được health check liên tiếp"
        print(f"VPN preflight: {reason}", flush=True)
        notify_vpn_event(
            notifier,
            "VPN KHÔNG ỔN ĐỊNH",
            {
                "Trạng thái": reason,
                "Service": service,
                "Host": host,
                "Hành động": "chuyển sang tối đa 3 lần tự bật lại",
            },
        )
    else:
        print(f"VPN preflight: unhealthy: {reason}", flush=True)
        notify_vpn_event(
            notifier,
            "VPN CHƯA BẬT",
            {
                "Trạng thái": reason,
                "Service": service,
                "Interface": interface,
                "Host": host,
                "Hành động": "sẽ tự động bật lại tối đa 3 lần",
            },
        )

    current_state = service_state(service, runner=runner)
    if current_state in {"active", "activating"}:
        print(
            f"{service} is already {current_state}; waiting for its internal reconnect "
            "before forcing a restart.",
            flush=True,
        )
        if wait_for_stable_vpn(
            service,
            interface,
            checks_per_attempt=checks_per_attempt,
            required_consecutive_checks=required_consecutive_checks,
            check_interval_seconds=check_interval_seconds,
            runner=runner,
            sleeper=sleeper,
        ):
            print("VPN preflight passed; crawler pipeline may start.", flush=True)
            notify_vpn_event(
                notifier,
                "VPN ĐÃ BẬT",
                {
                    "Trạng thái": "tự reconnect thành công và tunnel ổn định",
                    "Service": service,
                    "Interface": interface,
                    "Host": host,
                    "Crawler": "được phép chạy",
                },
            )
            return True

    for attempt in range(1, restart_attempts + 1):
        print(f"Restarting {service}: attempt {attempt}/{restart_attempts}", flush=True)
        notify_vpn_event(
            notifier,
            "ĐANG TỰ BẬT VPN",
            {
                "Lần thử": f"{attempt}/{restart_attempts}",
                "Service": service,
                "Interface": interface,
                "Host": host,
            },
        )
        if not restart_vpn(service, runner=runner):
            continue
        if wait_for_stable_vpn(
            service,
            interface,
            checks_per_attempt=checks_per_attempt,
            required_consecutive_checks=required_consecutive_checks,
            check_interval_seconds=check_interval_seconds,
            runner=runner,
            sleeper=sleeper,
        ):
            print("VPN preflight passed; crawler pipeline may start.", flush=True)
            notify_vpn_event(
                notifier,
                "VPN ĐÃ BẬT",
                {
                    "Trạng thái": "tunnel ổn định",
                    "Lần thử thành công": f"{attempt}/{restart_attempts}",
                    "Service": service,
                    "Interface": interface,
                    "Host": host,
                    "Crawler": "được phép chạy",
                },
            )
            return True

    failure_reason = vpn_health_reason(service, interface, runner=runner)[1]
    print(
        f"VPN preflight failed after {restart_attempts} restart attempts; "
        "crawler pipeline will not start.",
        file=sys.stderr,
        flush=True,
    )
    notify_vpn_event(
        notifier,
        "VPN KHÔNG THỂ BẬT",
        {
            "Trạng thái cuối": failure_reason,
            "Số lần thử": restart_attempts,
            "Service": service,
            "Interface": interface,
            "Host": host,
            "Crawler": "đã bị dừng, không chạy khi chưa có VPN",
        },
        possible_causes=[
            "Kiểm tra journalctl -u openvpn-client@japan; có thể server VPN từ chối certificate hoặc AUTH_FAILED.",
            "Kiểm tra tun0 và route redirect-gateway; crawler không được chạy qua IP public khi VPN chưa khỏe.",
        ],
    )
    return False


def main() -> int:
    """Run the bounded OpenVPN recovery and health-check workflow."""

    args = parse_args()
    try:
        dotenv_values = read_env_file(args.env_file)
    except (OSError, UnicodeError) as exc:
        print(f"Cannot read VPN notification environment: {exc}", file=sys.stderr)
        return 2

    host_environment = dict(dotenv_values)
    host_environment.update(os.environ)
    host_environment.setdefault("TELEGRAM_HOSTNAME", socket.gethostname())
    notifier = TelegramNotifier.from_env(host_environment)
    hostname = machine_name(host_environment)
    notify_vpn_event(
        notifier,
        "VPN KIỂM TRA BẮT ĐẦU",
        {
            "Service": args.service,
            "Interface": args.interface,
            "Số lần tự bật tối đa": args.restart_attempts,
            "Host": hostname,
            "Crawler": "chưa được phép chạy cho tới khi VPN khỏe",
        },
    )
    healthy = ensure_vpn(
        service=args.service,
        interface=args.interface,
        restart_attempts=args.restart_attempts,
        checks_per_attempt=args.checks_per_attempt,
        required_consecutive_checks=args.required_consecutive_checks,
        check_interval_seconds=args.check_interval_seconds,
        notifier=notifier,
        hostname=hostname,
    )
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
