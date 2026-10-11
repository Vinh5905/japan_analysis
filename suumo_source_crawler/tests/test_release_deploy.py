"""Exercise deploy failures entirely locally with Docker/systemd/SSH mocked."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import deploy_release as release
from scripts.runtime_lock import release_lock


class ReleaseDeployTests(unittest.TestCase):
    """Check that release packaging and failed installs preserve host data."""

    def setUp(self):
        """Create a fake host and archive without accessing a real VPS."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.target = self.root / "host"
        self.target.mkdir()
        self.units = self.root / "systemd"
        self.units.mkdir()
        self.env = '# config\nPOSTGRES_PASSWORD="keep-this-secret"\nSUUMO_CRAWLER_TAG=old-version\nSUUMO_VPN_BACKEND=docker\n'
        (self.target / ".env").write_text(self.env)
        (self.target / "docker-compose.release.yml").write_text("old compose")
        (self.target / "tmp").mkdir()
        (self.target / "tmp/suumo_links.txt").write_text("existing links")
        (self.units / release.TIMER).write_text("existing custom schedule")
        self.bundle = release.build_bundle("test-v2", self.root / "release.tar.gz")
        self.container_check = patch.object(release, "assert_no_crawler_containers")
        self.container_check.start()
        self.addCleanup(self.container_check.stop)
        self.infra_check = patch.object(
            release, "missing_infra_images", return_value=["postgres", "minio"]
        )
        self.infra_check.start()
        self.addCleanup(self.infra_check.stop)

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_container_migration_masks_host_auto_start_and_preserves_queue_schedule(
        self, commands, units
    ):
        """Changing backend backs up state without activating VPN, crawling, or resetting time."""
        (self.target / ".env").write_text(
            self.env.replace("SUUMO_VPN_BACKEND=docker\n", "")
        )
        from scripts.telegram_state import state_for

        state = state_for(self.target / ".env")
        state.set("automatic_start_at", 123)
        state.set("next_auto_at", 456)
        state.set("start_request", {"id": "confirmed", "area": {"area_id": 1}})
        commands.return_value = subprocess.CompletedProcess(
            [], 0, "-- private dump\n", ""
        )
        with (
            patch.object(release, "assert_host_vpn_stopped"),
            patch.object(release, "verify_container_vpn"),
            patch.object(
                release.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "enabled\n", ""),
            ),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                container_vpn=True,
            )
        self.assertIn("SUUMO_VPN_BACKEND=docker", (self.target / ".env").read_text())
        self.assertIn(
            'POSTGRES_PASSWORD="keep-this-secret"', (self.target / ".env").read_text()
        )
        self.assertEqual(state.get("next_auto_at"), 456)
        self.assertEqual(state.get("start_request")["id"], "confirmed")
        self.assertEqual(
            (self.units / release.TIMER).read_text(), "existing custom schedule"
        )
        backup = next((self.target / ".releases").iterdir())
        self.assertTrue((backup / "crawler-db.sql").exists())
        self.assertTrue((backup / "telegram-control.sqlite3").exists())
        self.assertEqual(
            json.loads((backup / "host-vpn-unit.json").read_text())["enabled"],
            "enabled",
        )
        calls = [c.args[0] for c in commands.call_args_list]
        self.assertIn(["systemctl", "mask", "openvpn-client@japan.service"], calls)
        self.assertFalse(
            any("restart" in c or (c[-1] == "vpn" and "up" in c) for c in calls)
        )

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_container_migration_failure_restores_files_and_host_enabled_state(
        self, commands, units
    ):
        """A wiring failure rolls back the backend and masking before resuming services."""
        self.env = self.env.replace("SUUMO_VPN_BACKEND=docker\n", "")
        (self.target / ".env").write_text(self.env)
        commands.return_value = subprocess.CompletedProcess([], 0, "-- dump\n", "")
        with (
            patch.object(release, "assert_host_vpn_stopped"),
            patch.object(
                release, "verify_container_vpn", side_effect=RuntimeError("bad wiring")
            ),
            patch.object(
                release.subprocess,
                "run",
                return_value=subprocess.CompletedProcess([], 0, "enabled\n", ""),
            ) as processes,
            self.assertRaisesRegex(RuntimeError, "bad wiring"),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                container_vpn=True,
            )
        self.assertEqual((self.target / ".env").read_text(), self.env)
        self.assertEqual(
            (self.target / "docker-compose.release.yml").read_text(), "old compose"
        )
        self.assertIn(
            ["systemctl", "unmask", "openvpn-client@japan.service"],
            [c.args[0] for c in processes.call_args_list],
        )
        self.assertIn(
            ["systemctl", "enable", "openvpn-client@japan.service"],
            [c.args[0] for c in processes.call_args_list],
        )

    @patch.object(release, "run")
    def test_host_tunnel_blocks_container_migration(self, commands):
        """Deployment refuses to alter a host that still has an active legacy VPN."""
        commands.return_value = subprocess.CompletedProcess(
            [], 0, "ActiveState=active\nMainPID=123\n", ""
        )
        with self.assertRaises(RuntimeError):
            release.assert_host_vpn_stopped()
        self.assertEqual(commands.call_count, 1)

    @patch.object(release, "run")
    def test_legacy_backend_requires_explicit_migration_before_any_host_action(
        self, commands
    ):
        """A forgotten migration flag cannot activate host VPN with Docker-only workers."""
        old = self.env.replace("SUUMO_VPN_BACKEND=docker\n", "")
        (self.target / ".env").write_text(old)
        with self.assertRaisesRegex(ValueError, "--container-vpn"):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        commands.assert_not_called()
        self.assertEqual((self.target / ".env").read_text(), old)
        self.assertEqual(
            (self.target / "docker-compose.release.yml").read_text(), "old compose"
        )

    def test_archive_is_complete_and_contains_no_secrets_or_data(self):
        """Inspect a real bundle rather than assuming its allowlist was followed."""
        with tarfile.open(self.bundle) as archive:
            names = archive.getnames()
            self.assertIn("suumo_source_crawler/scripts/ensure_openvpn.py", names)
            self.assertIn("suumo_source_crawler/scripts/stop_openvpn.py", names)
            self.assertIn("suumo_source_crawler/scripts/runtime_lock.py", names)
            self.assertIn(
                "suumo_source_crawler/crawler/crawler/telegram_notifier.py", names
            )
            self.assertIn(release.UNIT_PREFIX + release.TIMER, names)
            self.assertFalse(
                any(
                    ".env" in name
                    or "tmp/" in name
                    or "vpn_config/" in name
                    or name.endswith((".ovpn", ".conf"))
                    for name in names
                )
            )
        extracted = self.root / "unpack"
        self.assertEqual(release.unpack_bundle(self.bundle, extracted), "test-v2")
        self.assertEqual(
            (extracted / "docker-compose.release.yml").read_bytes(),
            (release.REPOSITORY_ROOT / "docker-compose.release.yml").read_bytes(),
        )

    @patch.object(
        release,
        "unit_state",
        side_effect=lambda name: "active" if name == release.TIMER else "inactive",
    )
    @patch.object(release, "run")
    def test_vpn_deploy_backs_up_state_preserves_schedule_and_does_not_start_vpn(
        self, commands, units
    ):
        """VPN rollout resumes existing dispatcher only after initialization succeeds."""
        from scripts.telegram_state import state_for

        state = state_for(self.target / ".env")
        state.set("automatic_start_at", 123)
        state.set("next_auto_at", 456)
        commands.return_value = subprocess.CompletedProcess(
            [], 0, stdout="-- private dump\n"
        )
        private = self.root / "private.tar"
        private.write_bytes(b"QA")
        with (
            patch.object(release, "initialize_vpn_pool") as initialize,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                enable_vpn_pool=True,
                vpn_archive=private,
            )
        self.assertEqual(initialize.call_args.args[-1], private)
        self.assertEqual(state.get("automatic_start_at"), 123)
        self.assertEqual(state.get("next_auto_at"), 456)
        self.assertEqual(
            (self.units / release.TIMER).read_text(), "existing custom schedule"
        )
        backup = next((self.target / ".releases").iterdir())
        self.assertTrue((backup / "crawler-db.sql").exists())
        self.assertTrue((backup / "telegram-control.sqlite3").exists())
        calls = [c.args[0] for c in commands.call_args_list]
        self.assertEqual(calls[-1], ["systemctl", "start", release.TIMER])
        self.assertFalse(any("openvpn-client@japan" in c for c in calls))

    @patch.object(release, "run")
    def test_vpn_initializer_applies_only_009_and_requires_shutdown(self, commands):
        """Initializing profiles never resets ward schedule or starts a VPN service."""
        directory = self.target / "docker/postgres/migrations"
        directory.mkdir(parents=True)
        text = (
            release.REPOSITORY_ROOT
            / "docker/postgres/migrations/009_crawl_vpn_pool.sql"
        ).read_text()
        (directory / "009_crawl_vpn_pool.sql").write_text(text)
        private = self.root / "private.tar"
        private.write_bytes(b"QA")
        with (
            patch("scripts.telegram_control.Host") as host,
            patch(
                "scripts.vpn_pool.receive", return_value={"registered": 23}
            ) as receive,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            host.return_value.vpn_stopped.return_value = True
            release.initialize_vpn_pool(self.target, ["docker", "compose"], private)
            self.assertEqual(commands.call_count, 1)
            self.assertEqual(commands.call_args.kwargs["input"], text)
            self.assertEqual(receive.call_count, 1)
            host.return_value.vpn_stopped.return_value = False
            with self.assertRaises(RuntimeError):
                release.initialize_vpn_pool(self.target, ["docker", "compose"], private)
            self.assertEqual(commands.call_count, 1)

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_ward_dispatch_backs_up_db_sqlite_and_enables_only_after_initialize(
        self, commands, units
    ):
        from scripts.telegram_state import state_for

        control = state_for(self.target / ".env")
        control.accept_update(99)
        commands.return_value = subprocess.CompletedProcess(
            [], 0, stdout="-- private QA dump\n"
        )
        with (
            patch.object(release, "initialize_ward_dispatch") as initialize,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                enable_ward_dispatch=True,
            )
        initialize.assert_called_once()
        backup = next((self.target / ".releases").iterdir())
        self.assertEqual(
            (backup / "crawler-db.sql").read_text(), "-- private QA dump\n"
        )
        self.assertEqual((backup / "crawler-db.sql").stat().st_mode & 0o777, 0o600)
        self.assertTrue((backup / "telegram-control.sqlite3").exists())
        self.assertEqual(control.get("offset"), 100)
        self.assertIn(
            "suumo-crawler-dispatch.service", (self.units / release.TIMER).read_text()
        )
        self.assertEqual(
            commands.call_args.args[0], ["systemctl", "enable", "--now", release.TIMER]
        )

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_verified_catalog_html_is_backed_up_and_passed_to_initializer(
        self, commands, units
    ):
        import hashlib

        html = self.root / "catalog.html"
        html.write_text("<html>QA catalogue</html>")
        commands.return_value = subprocess.CompletedProcess([], 0, stdout="-- dump\n")
        with (
            patch.object(release, "initialize_ward_dispatch") as initialize,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                enable_ward_dispatch=True,
                catalog_html=html,
            )
        self.assertEqual(initialize.call_args.args[-1], html)
        backup = next((self.target / ".releases").iterdir())
        self.assertEqual((backup / "osaka-city.html").read_bytes(), html.read_bytes())
        self.assertEqual(
            (backup / "osaka-city.sha256").read_text(),
            hashlib.sha256(html.read_bytes()).hexdigest(),
        )

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_ward_initialization_failure_restores_files_and_never_enables_timer(
        self, commands, units
    ):
        commands.return_value = subprocess.CompletedProcess([], 0, stdout="-- dump\n")
        with (
            patch.object(
                release,
                "initialize_ward_dispatch",
                side_effect=RuntimeError("sync failed"),
            ),
            patch.object(release.subprocess, "run"),
            self.assertRaisesRegex(RuntimeError, "sync failed"),
        ):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                enable_ward_dispatch=True,
            )
        self.assertEqual((self.target / ".env").read_text(), self.env)
        self.assertEqual(
            (self.units / release.TIMER).read_text(), "existing custom schedule"
        )
        self.assertFalse(any("enable" in c.args[0] for c in commands.call_args_list))

    @patch.object(release, "run")
    def test_initialize_only_new_migration_and_next_day_start(self, commands):
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo
        from scripts.telegram_state import state_for

        (self.target / "docker/postgres/migrations").mkdir(parents=True)
        text = (
            release.REPOSITORY_ROOT
            / "docker/postgres/migrations/008_crawl_areas_and_pipeline.sql"
        ).read_text()
        (
            self.target / "docker/postgres/migrations/008_crawl_areas_and_pipeline.sql"
        ).write_text(text)
        before = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        with (
            patch("scripts.area_catalog.refresh", return_value={"added": 0}),
            patch("scripts.telegram_control.Host"),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.initialize_ward_dispatch(self.target, ["docker", "compose"])
        self.assertEqual(commands.call_count, 1)
        self.assertEqual(commands.call_args.kwargs["input"], text)
        start = state_for(self.target / ".env").get("automatic_start_at")
        self.assertEqual(
            datetime.fromtimestamp(start, ZoneInfo("Asia/Ho_Chi_Minh")),
            before.replace(hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1),
        )

    def test_tampered_bundle_is_rejected_before_extracting(self):
        """Changed source bytes must not reach the host when checksum validation fails."""
        corrupt = self.root / "corrupt.tar.gz"
        with (
            tarfile.open(self.bundle) as source,
            tarfile.open(corrupt, "w:gz") as output,
        ):
            for item in source:
                data = source.extractfile(item).read()
                if item.name == "docker-compose.release.yml":
                    data += b"tampered"
                item.size = len(data)
                output.addfile(item, io.BytesIO(data))
        destination = self.root / "rejected"
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            release.unpack_bundle(corrupt, destination)
        self.assertFalse(destination.exists())

    def test_dry_run_makes_no_subprocess_calls(self):
        """The default command must not SSH, scp or contact Docker."""
        with (
            patch.object(release.subprocess, "run") as commands,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            release.deploy(
                "test-v2", "suumo-vps", Path("/opt/suumo-crawler"), False, False
            )
        commands.assert_not_called()

    def test_mutable_or_injected_tags_are_rejected(self):
        """Reject common accidental mutable tags and shell punctuation."""
        for tag in ("latest", "", "tag;echo", "v1/path"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                release.validate_tag(tag)

    def test_tag_update_preserves_credentials_and_comments(self):
        """Only the version assignment may change in the VPS .env."""
        updated = release.update_tag(self.env, "test-v2")
        self.assertEqual(updated, self.env.replace("old-version", "test-v2"))

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_pull_failure_does_not_modify_host(self, commands, state):
        """A registry outage must leave files, schedule and tag untouched."""
        commands.side_effect = subprocess.CalledProcessError(
            1, ["docker", "compose", "pull"]
        )
        with self.assertRaises(subprocess.CalledProcessError):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        self.assertEqual((self.target / ".env").read_text(), self.env)
        self.assertEqual(
            (self.target / "docker-compose.release.yml").read_text(), "old compose"
        )
        self.assertFalse((self.target / "suumo_source_crawler").exists())

    @patch.object(release, "unit_state", return_value="activating")
    @patch.object(release, "run")
    def test_running_service_blocks_deployment(self, commands, state):
        """Wait for an active preflight/crawl instead of stopping its VPN or container."""
        with self.assertRaisesRegex(RuntimeError, "activating"):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        commands.assert_not_called()
        self.assertEqual((self.target / ".env").read_text(), self.env)

    @patch.object(
        release,
        "unit_state",
        side_effect=lambda unit: "active" if unit == release.TIMER else "inactive",
    )
    @patch.object(release, "run")
    def test_install_preserves_custom_schedule_secrets_and_tmp(self, commands, state):
        """A successful update must retain operator configuration and resume its timer."""
        with contextlib.redirect_stdout(io.StringIO()):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        self.assertIn(
            'POSTGRES_PASSWORD="keep-this-secret"', (self.target / ".env").read_text()
        )
        self.assertIn("SUUMO_CRAWLER_TAG=test-v2", (self.target / ".env").read_text())
        self.assertEqual((self.target / ".env").stat().st_mode & 0o777, 0o600)
        self.assertEqual(
            (self.units / release.TIMER).read_text(), "existing custom schedule"
        )
        self.assertEqual(
            (self.target / "tmp/suumo_links.txt").read_text(), "existing links"
        )
        self.assertIn(str(self.target), (self.units / release.SERVICE).read_text())
        calls = [call.args[0] for call in commands.call_args_list]
        self.assertIn(["systemctl", "stop", release.TIMER], calls)
        self.assertIn(["systemctl", "start", release.TIMER], calls)
        self.assertFalse(
            any("openvpn-client@japan" in call or "run" in call for call in calls)
        )

    @patch.object(release.subprocess, "run")
    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_infra_failure_restores_previous_files_and_tag(
        self, commands, state, fallback
    ):
        """An unhealthy infra recreation must restore files while retaining host data."""

        def fake_run(command, **kwargs):
            """Fail the new infra health wait after the files have been installed."""
            if "--wait" in command:
                raise subprocess.CalledProcessError(1, command)

        commands.side_effect = fake_run
        with self.assertRaises(subprocess.CalledProcessError):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        self.assertEqual((self.target / ".env").read_text(), self.env)
        self.assertEqual(
            (self.target / "docker-compose.release.yml").read_text(), "old compose"
        )
        self.assertFalse((self.units / release.SERVICE).exists())
        self.assertEqual(
            (self.target / "tmp/suumo_links.txt").read_text(), "existing links"
        )
        self.assertTrue(list((self.target / ".releases").glob("*/paths.json")))

    def test_parallel_run_and_deploy_cannot_hold_the_lock(self):
        """The same lock serializes direct runner and deployment execution."""
        with (
            release_lock(self.target),
            self.assertRaisesRegex(RuntimeError, "release lock"),
        ):
            with release_lock(self.target):
                self.fail("Second lock unexpectedly acquired")

    @patch.object(release, "run")
    def test_manual_crawler_container_blocks_deployment(self, commands):
        """A direct compose-run crawl must be detected even when systemd is idle."""
        self.container_check.stop()
        commands.side_effect = [
            subprocess.CompletedProcess(
                [], 0, stdout=json.dumps({"name": "suumo_crawler_release"})
            ),
            subprocess.CompletedProcess([], 0, stdout="postgres\nminio\nsuumo-html\n"),
        ]
        with self.assertRaisesRegex(RuntimeError, "suumo-html"):
            release.assert_no_crawler_containers(["docker", "compose"])

    @patch.object(
        release,
        "unit_state",
        side_effect=lambda unit: "active" if unit == release.TIMER else "inactive",
    )
    @patch.object(release, "run")
    def test_pull_failure_restores_previously_active_timer(self, commands, state):
        """A failed update must not leave the schedule silently disabled."""

        def fake_run(command, **kwargs):
            """Fail registry access while letting timer stop/start succeed."""
            if "pull" in command:
                raise subprocess.CalledProcessError(1, command)

        commands.side_effect = fake_run
        with self.assertRaises(subprocess.CalledProcessError):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        calls = [call.args[0] for call in commands.call_args_list]
        self.assertEqual(calls[-1], ["systemctl", "start", release.TIMER])
        self.assertEqual((self.target / ".env").read_text(), self.env)

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_timer_replacement_requires_explicit_option(self, commands, state):
        """Only --update-timer may overwrite the operator's existing calendar."""
        with contextlib.redirect_stdout(io.StringIO()):
            release.apply_bundle(
                self.bundle,
                self.target,
                update_timer=True,
                systemd_directory=self.units,
            )
        self.assertIn("Asia/Ho_Chi_Minh", (self.units / release.TIMER).read_text())
        self.assertFalse(
            any(
                "enable" in call.args[0] or "start" in call.args[0]
                for call in commands.call_args_list
            )
        )

    @patch.object(
        release,
        "unit_state",
        side_effect=lambda unit: (
            "active" if unit == release.BOT_SERVICE else "inactive"
        ),
    )
    @patch.object(release, "run")
    def test_active_bot_restarts_after_install_preserving_sqlite(self, commands, state):
        from scripts.telegram_state import state_for

        control = state_for(self.target / ".env")
        control.accept_update(99)
        with contextlib.redirect_stdout(io.StringIO()):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        self.assertEqual(control.get("offset"), 100)
        calls = [call.args[0] for call in commands.call_args_list]
        self.assertIn(["systemctl", "stop", release.BOT_SERVICE], calls)
        self.assertEqual(calls[-1], ["systemctl", "start", release.BOT_SERVICE])
        self.assertFalse(any("enable" in call for call in calls))
        self.assertIn(str(self.target), (self.units / release.BOT_SERVICE).read_text())

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_explicit_enable_changes_only_control_flag_and_tag(self, commands, state):
        (self.target / ".env").write_text(self.env + "TELEGRAM_CONTROL_ENABLED=false\n")
        with contextlib.redirect_stdout(io.StringIO()):
            release.apply_bundle(
                self.bundle,
                self.target,
                systemd_directory=self.units,
                enable_telegram_bot=True,
            )
        self.assertEqual(
            (self.target / ".env").read_text(),
            self.env.replace("old-version", "test-v2")
            + "TELEGRAM_CONTROL_ENABLED=true\n",
        )
        self.assertEqual(
            commands.call_args.args[0],
            ["systemctl", "enable", "--now", release.BOT_SERVICE],
        )

    @patch.object(
        release,
        "unit_state",
        side_effect=lambda unit: (
            "active" if unit == release.BOT_SERVICE else "inactive"
        ),
    )
    @patch.object(release, "run")
    def test_failed_pull_resumes_old_active_bot(self, commands, state):
        def failed_pull(command, **kwargs):
            if "pull" in command:
                raise subprocess.CalledProcessError(1, command)

        commands.side_effect = failed_pull
        with self.assertRaises(subprocess.CalledProcessError):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        self.assertEqual(
            commands.call_args.args[0], ["systemctl", "start", release.BOT_SERVICE]
        )
        self.assertEqual((self.target / ".env").read_text(), self.env)

    @patch.object(release, "run")
    @patch.object(release.subprocess, "run")
    def test_infra_cache_checks_exact_configured_tags(self, inspect, commands):
        self.infra_check.stop()
        commands.return_value = subprocess.CompletedProcess(
            [],
            0,
            stdout=json.dumps(
                {
                    "services": {
                        "postgres": {"image": "postgres:configured"},
                        "minio": {"image": "minio/minio:configured"},
                    }
                }
            ),
        )
        inspect.side_effect = [
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 1),
        ]
        self.assertEqual(release.missing_infra_images(["docker", "compose"]), ["minio"])
        self.assertEqual(
            [call.args[0][-1] for call in inspect.call_args_list],
            ["postgres:configured", "minio/minio:configured"],
        )

    @patch.object(release, "unit_state", return_value="inactive")
    @patch.object(release, "run")
    def test_cached_infra_deploy_pulls_only_new_crawler(self, commands, state):
        release.missing_infra_images.return_value = []
        with contextlib.redirect_stdout(io.StringIO()):
            release.apply_bundle(self.bundle, self.target, systemd_directory=self.units)
        pulls = [
            call.args[0] for call in commands.call_args_list if "pull" in call.args[0]
        ]
        self.assertEqual(len(pulls), 1)
        self.assertEqual(pulls[0][-2:], ["pull", "crawler-init"])


if __name__ == "__main__":
    unittest.main()
