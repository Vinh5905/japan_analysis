"""Offline checks for isolation, fail-closed rules, Docker lifecycle, and rotation."""

import copy
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.docker_vpn import DockerVpn, docker_backend
from scripts import vpn_pool
from scripts.telegram_state import ControlState
from scripts.telegram_state import state_for
from scripts import stop_openvpn as shutdown
from vpn import container_vpn

CONFIG = {
    "name": "qa",
    "services": {
        "vpn": {"networks": {"private": {}}, "image": "qa"},
        **{
            name: {"network_mode": "service:vpn"}
            for name in ("suumo-links", "suumo-html", "suumo-page", "suumo-rerun-html")
        },
    },
    "networks": {"private": {"name": "qa_private"}},
}
DATA = b"client\ndev tun\nproto tcp\nremote 192.0.2.1 443\ncipher AES-128-CBC\n<ca>test</ca>\n<cert>test</cert>\n<key>test</key>\n"


class DockerVpnTests(unittest.TestCase):
    """Exercise failed commands without touching a real container or tunnel."""

    def setUp(self):
        """Create a private runtime and fake the minimal Docker control plane."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.host = Mock(
            env_file=self.root / ".env",
            compose=["docker", "compose"],
            values={"SUUMO_VPN_BACKEND": "docker"},
        )
        self.commands = []
        self.running = []
        self.failed_ps = False

        def runner(argv, timeout):
            """Return deterministic Docker metadata and retain command ordering."""
            self.commands.append(argv)
            output = ""
            code = 0
            if "config" in argv:
                output = json.dumps(CONFIG)
            elif argv[:2] == ["docker", "ps"]:
                output = "\n".join(self.running)
                code = int(self.failed_ps)
            elif "ps" in argv:
                output = argv[-1] + "-id"
            elif "inspect" in argv:
                output = json.dumps(
                    {
                        "qa_private": {
                            "IPAddress": "172.25.0.2"
                            if argv[-1].startswith("postgres")
                            else "172.25.0.3"
                        }
                    }
                )
            elif argv[:2] == ["docker", "stop"]:
                self.running = []
            return subprocess.CompletedProcess(argv, code, output, "")

        self.runner = runner
        self.controller = DockerVpn(self.host, runner)

    def test_prepare_freezes_profile_internal_hosts_and_tunnel_dns(self):
        """No SSH bypass, host config, credentials, or Docker DNS proxy enters the runtime."""
        self.controller.prepare(
            DATA + b"route 198.51.100.1 255.255.255.255 net_gateway\n", "a.ovpn"
        )
        root = self.controller.runtime
        config = (root / "config.ovpn").read_text()
        self.assertIn("<key>test</key>", config)
        self.assertNotIn("net_gateway", config)
        self.assertIn("data-ciphers-fallback AES-128-CBC", config)
        self.assertIn("172.25.0.2 postgres", (root / "hosts").read_text())
        self.assertNotIn("127.0.0.11", (root / "resolv.conf").read_text())
        self.assertEqual((root / "config.ovpn").stat().st_mode & 0o777, 0o600)
        self.assertEqual(root.stat().st_mode & 0o777, 0o700)

    def test_reject_host_network_privileged_worker_or_disconnected_infra(self):
        """Reject wiring that could affect SSH or evade the sidecar firewall."""
        for name, field, value in [
            ("vpn", "network_mode", "host"),
            ("vpn", "privileged", True),
            ("suumo-html", "network_mode", "bridge"),
            ("suumo-page", "cap_add", ["NET_ADMIN"]),
        ]:
            config = copy.deepcopy(CONFIG)
            config["services"][name][field] = value
            runner = Mock(
                return_value=subprocess.CompletedProcess([], 0, json.dumps(config), "")
            )
            with self.assertRaises(RuntimeError):
                DockerVpn(self.host, runner)
        with patch.object(
            self.controller,
            "call",
            return_value=subprocess.CompletedProcess([], 0, "{}", ""),
        ):
            with self.assertRaises(RuntimeError):
                self.controller.internal_ip("postgres")

    def test_start_does_not_pull_or_restart_dependencies(self):
        """The worker phase cannot silently recreate the VPN or change its frozen context."""
        self.controller.start()
        self.assertIn("--no-deps", self.commands[-1])
        self.assertIn("--force-recreate", self.commands[-1])
        self.assertEqual(self.commands[-1][-1], "vpn")
        self.assertFalse(
            any("systemctl" in c or c[:1] == ["ip"] for c in self.commands)
        )

    def test_stop_scoped_container_and_reject_unknown_docker_state(self):
        """A daemon failure cannot turn into confirmed cleanup."""
        self.running = ["vpn-id"]
        self.assertTrue(self.controller.stop(sleeper=lambda seconds: None))
        self.assertIn(["docker", "stop", "--time", "10", "vpn-id"], self.commands)
        self.assertIn(["docker", "rm", "vpn-id"], self.commands)
        self.failed_ps = True
        with self.assertRaises(RuntimeError):
            self.controller.stopped()

    def test_firewall_has_no_direct_dns_or_established_flow_exception(self):
        """Only the exact VPN port and internal DB/MinIO ports bypass the tunnel."""
        rules = container_vpn.firewall_rules(
            {
                "remote": "192.0.2.1",
                "protocol": "tcp",
                "port": 443,
                "postgres": "172.25.0.2",
                "minio": "172.25.0.3",
            }
        )
        text = json.dumps(rules)
        self.assertNotIn("ESTABLISHED", text)
        self.assertNotIn("53", text)
        self.assertNotIn("0.0.0.0/0", text)
        self.assertIn('--dport", "5432', text)
        commands = []
        with patch.object(
            container_vpn, "command", side_effect=lambda args: commands.append(args)
        ):
            container_vpn.install_firewall(
                {
                    "remote": "192.0.2.1",
                    "protocol": "udp",
                    "port": 1194,
                    "postgres": "172.25.0.2",
                    "minio": "172.25.0.3",
                }
            )
        self.assertEqual(commands[0], ["iptables", "-w", "2", "-P", "OUTPUT", "DROP"])
        self.assertIn(["ip6tables", "-w", "2", "-P", "OUTPUT", "DROP"], commands)

    def test_backend_and_failed_health_are_explicit(self):
        """The legacy fallback is compatible and invalid configuration fails closed."""
        self.assertFalse(docker_backend({}))
        self.assertTrue(docker_backend({"SUUMO_VPN_BACKEND": "docker"}))
        with self.assertRaises(ValueError):
            docker_backend({"SUUMO_VPN_BACKEND": "unknown"})
        self.assertFalse(self.controller.health()[0])
        self.assertFalse(container_vpn.health())

    def test_docker_rotation_preserves_one_run_and_never_calls_host_vpn(self):
        """Timeout/fallback waits for verified sidecar cleanup and keeps the run identity."""
        directory = self.root / "vpn_config"
        directory.mkdir()
        for name in ("a.ovpn", "b.ovpn"):
            (directory / name).write_bytes(DATA)
        self.host.values["VPN_CONFIG_DIR"] = str(directory)
        self.host.query.return_value = [
            {**r, "vpn_id": i + 1} for i, r in enumerate(vpn_pool.inventory(directory))
        ]
        self.host.vpn_stopped.return_value = True
        state = ControlState(self.root / "state/test.sqlite3")
        state.launch({"area_id": 1, "display_name": "Yodogawa"}, "manual")
        state.begin(run_id=42, created_at=0)
        controller = Mock()
        controller.stop.return_value = True
        clock = [0]

        def sleep(seconds):
            """Advance a deterministic clock without waiting."""
            clock[0] += seconds

        controller.health.side_effect = [(False, "down")] * 30 + [(True, "ready")] * 3
        attempts = [
            {"attempt_id": i + 1, "vpn_id": i + 1, "run_id": 42} for i in range(2)
        ]
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("scripts.docker_vpn.DockerVpn", return_value=controller),
            patch.object(vpn_pool, "start_attempt", side_effect=attempts),
            patch.object(vpn_pool, "finish_attempt", return_value=attempts[0]),
            patch("scripts.ensure_openvpn.restart_vpn") as legacy,
            patch("scripts.stop_openvpn.stop_vpn") as legacy_stop,
        ):
            self.assertTrue(
                vpn_pool.select_vpn(
                    self.host,
                    state,
                    sleeper=sleep,
                    monotonic=lambda: clock[0],
                    config_target=self.root / "host.conf",
                )
            )
        legacy.assert_not_called()
        legacy_stop.assert_not_called()
        self.assertEqual(controller.start.call_count, 2)
        self.assertEqual(controller.stop.call_count, 2)
        self.assertEqual(state.get("pipeline")["run_id"], "42")
        self.assertEqual(state.get("pipeline")["vpn"]["filename"], "b.ovpn")
        self.assertFalse((self.root / "host.conf").exists())

    def test_cleanup_hook_stops_workers_before_vpn_and_blocks_unconfirmed_cleanup(self):
        """ExecStopPost persists/wakes only after worker shutdown and checks both backends."""
        for outcome in ("healthy", "host_active", "docker_error"):
            with self.subTest(outcome=outcome):
                env = self.root / outcome / ".env"
                env.parent.mkdir()
                env.write_text("SUUMO_VPN_BACKEND=docker\n")
                state = state_for(env)
                state.launch({"area_id": 1, "display_name": "Yodogawa"}, "manual")
                state.begin(run_id=42, created_at=0)
                state.progress(
                    "awaiting_vpn_cleanup",
                    completion={"summaries": {}, "started_at": "now", "hostname": "qa"},
                )
                args = argparse.Namespace(
                    env_file=env,
                    compose_file=env.parent / "compose",
                    lock_held=True,
                    service="openvpn-client@japan",
                    interface="tun0",
                    stop_attempts=3,
                    checks_per_attempt=3,
                    required_consecutive_checks=3,
                    check_interval_seconds=0,
                )
                order = []
                controller = Mock()

                def stop():
                    """Record sidecar teardown and simulate a failed Docker inspection."""
                    order.append("vpn")
                    if outcome == "docker_error":
                        raise RuntimeError("Docker inspection unavailable")
                    return True

                controller.stop.side_effect = stop
                with (
                    patch.dict(os.environ, {"SERVICE_RESULT": "success"}, clear=True),
                    patch.object(shutdown, "parse_args", return_value=args),
                    patch.object(
                        shutdown.TelegramNotifier, "from_env", return_value=Mock()
                    ),
                    patch.object(
                        shutdown,
                        "finish_crawler_containers",
                        side_effect=lambda *args: order.append("workers"),
                    ),
                    patch("scripts.docker_vpn.DockerVpn", return_value=controller),
                    patch.object(
                        shutdown,
                        "vpn_stopped_reason",
                        return_value=(outcome == "healthy", "host state"),
                    ),
                    patch.object(shutdown, "stop_vpn") as legacy,
                    patch("scripts.crawl_dispatcher.persist_finish") as persist,
                    patch("scripts.crawl_dispatcher.wake") as wake,
                ):
                    self.assertEqual(shutdown.main(), 0 if outcome == "healthy" else 1)
                self.assertEqual(order, ["workers", "vpn"])
                legacy.assert_not_called()
                self.assertEqual(persist.call_args.args[-1], outcome == "healthy")
                self.assertEqual(wake.call_count, 0 if outcome == "docker_error" else 1)


if __name__ == "__main__":
    unittest.main()
