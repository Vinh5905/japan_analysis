from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ensure_openvpn import ensure_vpn, vpn_health_reason  # noqa: E402


def completed(command: Sequence[str], returncode: int = 0, stdout: str = ""):
    """Build a small CompletedProcess result for command-runner tests."""

    return subprocess.CompletedProcess(list(command), returncode, stdout=stdout, stderr="")


class StatefulVpnRunner:
    """Simulate systemctl/ip state before and after a restart request."""

    def __init__(self, become_healthy_after_restart: bool = True):
        self.healthy = False
        self.become_healthy_after_restart = become_healthy_after_restart
        self.restart_count = 0
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str]):
        command_tuple = tuple(command)
        self.commands.append(command_tuple)
        if command_tuple[:3] == ("systemctl", "restart", "--no-block"):
            self.restart_count += 1
            self.healthy = self.become_healthy_after_restart
            return completed(command)
        if command_tuple[:2] == ("systemctl", "reset-failed"):
            return completed(command)
        if command_tuple[:2] == ("systemctl", "is-active"):
            if self.healthy:
                return completed(command, stdout="active\n")
            return completed(command, returncode=3, stdout="inactive\n")
        if command_tuple[:5] == ("ip", "-o", "link", "show", "dev"):
            output = "7: tun0: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1500\n"
            return completed(command, stdout=output if self.healthy else "")
        if command_tuple[:4] == ("ip", "-4", "route", "show"):
            network = command_tuple[4]
            output = f"{network} via 10.240.0.2 dev tun0\n"
            return completed(command, stdout=output if self.healthy else "")
        raise AssertionError(f"Unexpected command: {command_tuple}")


class InternallyRecoveringVpnRunner(StatefulVpnRunner):
    """Simulate an active OpenVPN process that creates tun0 after several polls."""

    def __init__(self, recover_after_service_checks: int):
        super().__init__(become_healthy_after_restart=False)
        self.service_check_count = 0
        self.recover_after_service_checks = recover_after_service_checks

    def __call__(self, command: Sequence[str]):
        command_tuple = tuple(command)
        if command_tuple[:2] == ("systemctl", "is-active"):
            self.commands.append(command_tuple)
            self.service_check_count += 1
            if self.service_check_count >= self.recover_after_service_checks:
                self.healthy = True
            return completed(command, stdout="active\n")
        return super().__call__(command)


class ActiveUnhealthyVpnRunner(StatefulVpnRunner):
    """Simulate an active service whose tunnel and redirect routes never appear."""

    def __call__(self, command: Sequence[str]):
        command_tuple = tuple(command)
        if command_tuple[:2] == ("systemctl", "is-active"):
            self.commands.append(command_tuple)
            return completed(command, stdout="active\n")
        return super().__call__(command)


class RecordingNotifier:
    """Capture notification text without contacting Telegram in unit tests."""

    def __init__(self):
        self.messages: list[str] = []

    def send_message(self, message: str):
        self.messages.append(message)


class EnsureOpenVpnTests(unittest.TestCase):
    def test_health_requires_service_interface_and_redirect_routes(self):
        runner = StatefulVpnRunner()
        runner.healthy = True

        healthy, reason = vpn_health_reason(
            "openvpn-client@japan",
            "tun0",
            runner=runner,
        )

        self.assertTrue(healthy)
        self.assertIn("redirect routes", reason)

    def test_inactive_vpn_is_restarted_and_checked_repeatedly(self):
        runner = StatefulVpnRunner(become_healthy_after_restart=True)

        healthy = ensure_vpn(
            service="openvpn-client@japan",
            interface="tun0",
            restart_attempts=3,
            checks_per_attempt=5,
            required_consecutive_checks=3,
            check_interval_seconds=0,
            runner=runner,
            sleeper=lambda _: None,
        )

        self.assertTrue(healthy)
        self.assertEqual(runner.restart_count, 1)

    def test_active_service_gets_time_for_internal_reconnect_before_restart(self):
        runner = InternallyRecoveringVpnRunner(recover_after_service_checks=4)

        healthy = ensure_vpn(
            service="openvpn-client@japan",
            interface="tun0",
            restart_attempts=3,
            checks_per_attempt=8,
            required_consecutive_checks=3,
            check_interval_seconds=0,
            runner=runner,
            sleeper=lambda _: None,
        )

        self.assertTrue(healthy)
        self.assertEqual(runner.restart_count, 0)

    def test_pipeline_preflight_fails_after_bounded_restarts(self):
        runner = StatefulVpnRunner(become_healthy_after_restart=False)

        healthy = ensure_vpn(
            service="openvpn-client@japan",
            interface="tun0",
            restart_attempts=3,
            checks_per_attempt=2,
            required_consecutive_checks=2,
            check_interval_seconds=0,
            runner=runner,
            sleeper=lambda _: None,
        )

        self.assertFalse(healthy)
        self.assertEqual(runner.restart_count, 3)

    def test_vpn_lifecycle_notifications_are_emitted(self):
        runner = StatefulVpnRunner(become_healthy_after_restart=True)
        notifier = RecordingNotifier()

        healthy = ensure_vpn(
            service="openvpn-client@japan",
            interface="tun0",
            restart_attempts=3,
            checks_per_attempt=3,
            required_consecutive_checks=2,
            check_interval_seconds=0,
            runner=runner,
            sleeper=lambda _: None,
            notifier=notifier,
            hostname="vps-test",
        )

        self.assertTrue(healthy)
        self.assertTrue(any("VPN CHƯA BẬT" in message for message in notifier.messages))
        self.assertTrue(any("ĐANG TỰ BẬT VPN" in message for message in notifier.messages))
        self.assertTrue(any("VPN ĐÃ BẬT" in message for message in notifier.messages))

    def test_unstable_active_vpn_still_uses_all_restart_attempts(self):
        runner = ActiveUnhealthyVpnRunner(become_healthy_after_restart=False)
        notifier = RecordingNotifier()

        healthy = ensure_vpn(
            service="openvpn-client@japan",
            interface="tun0",
            restart_attempts=3,
            checks_per_attempt=2,
            required_consecutive_checks=2,
            check_interval_seconds=0,
            runner=runner,
            sleeper=lambda _: None,
            notifier=notifier,
            hostname="vps-test",
        )

        self.assertFalse(healthy)
        self.assertEqual(runner.restart_count, 3)
        self.assertTrue(any("VPN KHÔNG THỂ BẬT" in message for message in notifier.messages))


if __name__ == "__main__":
    unittest.main()
