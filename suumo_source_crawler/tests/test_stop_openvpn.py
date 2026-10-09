"""Check confirmed VPN shutdown and lifecycle cleanup without touching any host services."""

import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import stop_openvpn as shutdown
from scripts import run_release_pipeline as pipeline


def completed(command, returncode=0, stdout=""):
    """Build fake host command output for shutdown tests."""
    return subprocess.CompletedProcess(list(command), returncode, stdout=stdout, stderr="")


class FakeVpnRunner:
    """Model async service stop separately from tunnel and route cleanup."""

    def __init__(self, stopped=True, tunnel_up=False, routes=False, ipv6_routes=False, pending_checks=0):
        """Configure the state that host queries report, without running systemctl/ip."""
        self.stopped = stopped
        self.tunnel_up = tunnel_up
        self.routes = routes
        self.ipv6_routes = ipv6_routes
        self.pending_checks = pending_checks
        self.stop_requests = 0
        self.queries = 0

    def __call__(self, command):
        """Return JSON network state and record every requested service stop."""
        command = tuple(command)
        if command[:3] == ("systemctl", "stop", "--no-block"):
            self.stop_requests += 1
            return completed(command)
        if command[:2] == ("systemctl", "show"):
            self.queries += 1
            if self.pending_checks > 0:
                self.pending_checks -= 1
                return completed(command, stdout="ActiveState=deactivating\nMainPID=123\n")
            return completed(command, stdout="ActiveState=inactive\nMainPID=0\n" if self.stopped else "ActiveState=active\nMainPID=123\n")
        if command == ("ip", "-j", "link", "show"):
            links = [{"ifname": "tun0", "flags": ["UP"]}] if self.tunnel_up else []
            return completed(command, stdout=json.dumps(links))
        if command[:4] in {("ip", "-j", "-4", "route"), ("ip", "-j", "-6", "route")}:
            routes = self.ipv6_routes if command[2] == "-6" else self.routes
            return completed(command, stdout=json.dumps([{"dev": "tun0"}] if routes else []))
        raise AssertionError(f"Unexpected host command: {command}")


class RecordingNotifier:
    """Collect Telegram messages locally."""

    def __init__(self):
        """Initialize the captured event list."""
        self.messages = []

    def send_message(self, message):
        """Record a notification instead of contacting Telegram."""
        self.messages.append(message)


class StopOpenVpnTests(unittest.TestCase):
    """Require actual tunnel/process/route evidence before reporting shutdown."""

    def test_async_shutdown_waits_for_three_confirmations(self):
        """A successful stop command alone must not complete the cleanup."""
        runner = FakeVpnRunner(pending_checks=2)
        notifier = RecordingNotifier()
        with contextlib.redirect_stdout(io.StringIO()):
            result = shutdown.stop_vpn("openvpn-client@japan", "tun0", checks_per_attempt=6,
                                       runner=runner, sleeper=lambda _: None, notifier=notifier)
        self.assertTrue(result)
        self.assertEqual(runner.queries, 5)
        self.assertEqual(runner.stop_requests, 1)
        self.assertIn("ĐÃ XÁC NHẬN", notifier.messages[-1])

    def test_stopped_service_is_not_enough_with_live_tunnel_or_routes(self):
        """A lingering tunnel or either IP family's route prevents a false success."""
        for options in ({"tunnel_up": True}, {"routes": True}, {"ipv6_routes": True}, {"stopped": False}):
            with self.subTest(options=options):
                stopped, _ = shutdown.vpn_stopped_reason("openvpn-client@japan", "tun0", FakeVpnRunner(**options))
                self.assertFalse(stopped)

    def test_shutdown_retries_and_fails_when_service_stays_active(self):
        """Exhausted retries produce failure and no confirmed-shutdown notification."""
        runner = FakeVpnRunner(stopped=False)
        notifier = RecordingNotifier()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = shutdown.stop_vpn("openvpn-client@japan", "tun0", checks_per_attempt=3,
                                       runner=runner, sleeper=lambda _: None, notifier=notifier)
        self.assertFalse(result)
        self.assertEqual(runner.stop_requests, 3)
        self.assertIn("KHÔNG XÁC NHẬN", notifier.messages[-1])

    def test_query_error_is_not_treated_as_absent_tunnel(self):
        """Permissions/command failures must not masquerade as a closed VPN."""
        def failed_query(command):
            """Simulate a failed ip query after the process is stopped."""
            if tuple(command)[:2] == ("systemctl", "show"):
                return completed(command, stdout="ActiveState=inactive\nMainPID=0\n")
            return completed(command, 1)
        self.assertFalse(shutdown.vpn_stopped_reason("openvpn-client@japan", "tun0", failed_query)[0])

    def test_command_timeout_fails_cleanup(self):
        """A hung systemctl call must return failure instead of claiming shutdown."""
        def timeout(command):
            """Simulate bounded command execution timing out."""
            raise subprocess.TimeoutExpired(command, 30)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertFalse(shutdown.stop_vpn("openvpn-client@japan", "tun0", runner=timeout))

    def test_leftover_pipeline_container_is_stopped_before_vpn(self):
        """Cleanup affects crawler tasks in this project, retaining Postgres/MinIO."""
        commands = []
        def fake_run(command):
            """Return one orphan crawler followed by an empty crawler population."""
            commands.append(tuple(command))
            if "config" in command:
                return completed(command, stdout=json.dumps({"name": "suumo_crawler_release"}))
            if tuple(command)[:2] == ("docker", "ps"):
                text = "abc suumo-html\npq postgres\nmio minio\n" if len(commands) == 2 else "pq postgres\nmio minio\n"
                return completed(command, stdout=text)
            return completed(command)
        with contextlib.redirect_stdout(io.StringIO()):
            shutdown.finish_crawler_containers(Path("compose.yml"), Path(".env"), fake_run)
        self.assertIn(("docker", "stop", "--time", "10", "abc"), commands)
        self.assertFalse(any("pq" in command or "mio" in command for command in commands))

    def test_failed_container_stop_prevents_vpn_shutdown(self):
        """Do not switch a still-running crawler onto the public route."""
        def fake_run(command):
            """Simulate a task that Docker refuses to stop."""
            if "config" in command:
                return completed(command, stdout=json.dumps({"name": "suumo_crawler_release"}))
            if "ps" in command:
                return completed(command, stdout="abc suumo-html\n")
            return completed(command, 1)
        with self.assertRaisesRegex(RuntimeError, "Cannot stop"), contextlib.redirect_stdout(io.StringIO()):
            shutdown.finish_crawler_containers(Path("compose.yml"), Path(".env"), fake_run)


class ManualPipelineVpnTests(unittest.TestCase):
    """Manual execution has the same preflight/final cleanup guarantees as systemd."""

    def setUp(self):
        from unittest.mock import MagicMock
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        (self.base / ".env").write_text("SUUMO_SEARCH_URL=https://suumo.jp/chintai/?sc=27123\n")
        host = MagicMock()
        host.busy.return_value = False
        host.unresolved.return_value = None
        host.values = {"SUUMO_SEARCH_URL": "https://suumo.jp/chintai/?sc=27123"}
        host.areas.return_value = [{"area_id":1,"sc":"27123","runs":0,"last_run":None,"today_runs":0}]
        for patcher in (patch("scripts.telegram_control.Host", return_value=host), patch("scripts.area_catalog.refresh")):
            patcher.start()
            self.addCleanup(patcher.stop)

    def args(self):
        """Build manual CLI paths without reading an actual .env."""
        return argparse.Namespace(compose_file=self.base / "compose.yml", env_file=self.base / ".env",
                                  vpn_service="openvpn-client@japan", vpn_interface="tun0")

    @patch.object(pipeline, "run_pipeline", return_value=0)
    @patch.object(pipeline, "run_command")
    def test_success_waits_for_shutdown(self, command, crawl):
        """Successful crawling still fails overall when shutdown cannot be confirmed."""
        command.side_effect = [pipeline.CommandResult(0, ""), pipeline.CommandResult(1, "shutdown failed")]
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(pipeline.run_with_vpn(self.args()), 1)
        self.assertIn("stop_openvpn.py", command.call_args.args[0][1])

    @patch.object(pipeline, "run_pipeline", return_value=17)
    @patch.object(pipeline, "run_command")
    def test_crawler_failure_still_closes_vpn_and_preserves_exit_code(self, command, crawl):
        """Closing the VPN must not hide the original crawler failure."""
        command.side_effect = [pipeline.CommandResult(0, ""), pipeline.CommandResult(0, "")]
        self.assertEqual(pipeline.run_with_vpn(self.args()), 17)
        self.assertEqual(command.call_args.args[2]["SERVICE_RESULT"], "exit-code")

    @patch.object(pipeline, "run_pipeline")
    @patch.object(pipeline, "run_command")
    def test_preflight_failure_skips_crawl_but_runs_cleanup(self, command, crawl):
        """A partially opened tunnel must be cleaned up after preflight fails."""
        command.side_effect = [pipeline.CommandResult(1, "VPN unhealthy"), pipeline.CommandResult(0, "")]
        self.assertEqual(pipeline.run_with_vpn(self.args()), 1)
        crawl.assert_not_called()
        self.assertEqual(command.call_count, 2)

    @patch.object(pipeline, "run_pipeline", side_effect=RuntimeError("unexpected failure"))
    @patch.object(pipeline, "run_command", return_value=pipeline.CommandResult(0, ""))
    def test_python_exception_also_runs_cleanup(self, command, crawl):
        """finally cleanup must execute even before normal error reporting finishes."""
        with self.assertRaisesRegex(RuntimeError, "unexpected failure"):
            pipeline.run_with_vpn(self.args())
        self.assertEqual(command.call_count, 2)


if __name__ == "__main__":
    unittest.main()
