"""Exercise host fail-fast accounting gates with all external commands mocked."""

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import run_release_pipeline as pipeline
from scripts.telegram_state import state_for


class VpnRunnerTests(unittest.TestCase):
    def run_case(self, outcome):
        """Inject a zero-exit spider outcome and inspect which later stages run."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {}, clear=True),
        ):
            root = Path(tmp)
            env = root / ".env"
            env.write_text("")
            compose = root / "docker-compose.release.yml"
            compose.write_text("")
            state = state_for(env)
            state.launch(
                {"area_id": 1, "search_url": "https://suumo.jp/?sc=27123"}, "manual"
            )
            state.begin(run_id=42, created_at=0)
            state.progress("vpn_ready", vpn={"vpn_id": 2, "filename": "b.ovpn"})
            directory = root / "tmp/telegram/42"
            commands = []

            def command(argv, *args):
                """Create the summary that a real spider would leave in its tmp volume."""
                commands.append(argv)
                name = argv[-1].replace("-", "_")
                if name in pipeline.SPIDER_NAMES:
                    directory.mkdir(parents=True, exist_ok=True)
                    if outcome == "marker":
                        (directory / "vpn_accounting_failed").touch()
                    if outcome != "missing":
                        (directory / (name + ".json")).write_text(
                            json.dumps(
                                {
                                    "job_name": name,
                                    "status": "failed"
                                    if outcome == "failed"
                                    else "completed",
                                    "close_reason": "finished",
                                }
                            )
                        )
                return pipeline.CommandResult(0, "")

            with (
                patch.object(pipeline, "run_command", side_effect=command),
                patch.object(pipeline.TelegramNotifier, "from_env"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = pipeline.run_pipeline(
                    SimpleNamespace(compose_file=compose, env_file=env)
                )
            return result, commands, state.get("pipeline")

    def test_zero_exit_accounting_marker_stops_before_html(self):
        result, commands, state = self.run_case("marker")
        self.assertEqual(result, 1)
        self.assertEqual(len(commands), 3)
        self.assertEqual(state["status"], "failed")
        self.assertIsNone(state["completion"])

    def test_zero_exit_failed_or_missing_summary_stops(self):
        for outcome in ("failed", "missing"):
            with self.subTest(outcome=outcome):
                result, commands, state = self.run_case(outcome)
                self.assertEqual(result, 1)
                self.assertEqual(len(commands), 3)

    def test_verified_vpn_context_reaches_all_stages_and_waits_cleanup(self):
        result, commands, state = self.run_case("success")
        self.assertEqual(result, 0)
        self.assertEqual(len(commands), 5)
        self.assertTrue(all("SUUMO_VPN_ID=2" in c for c in commands[2:]))
        self.assertEqual(state["step"], "awaiting_vpn_cleanup")
        self.assertFalse(state["cleanup_confirmed"])


if __name__ == "__main__":
    unittest.main()
