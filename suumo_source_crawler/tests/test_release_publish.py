"""Verify the combined release command without Docker, SSH, or real publication."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class PublishDeployTests(unittest.TestCase):
    """Run real recursive make with disposable command shims."""
    def invoke(self, build_exit=0):
        """Capture orchestration order while preventing all external side effects."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / 'order.log'
            python = root / 'python3'
            python.write_text('#!/bin/sh\ncase "$*" in *--apply*) printf "DEPLOY\\n";; *) printf "PLAN\\n";; esac >> "$SUUMO_MAKE_QA_LOG"\n')
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\ncase "$*" in *"buildx build"*) printf "BUILD\\n" >> "$SUUMO_MAKE_QA_LOG"; exit "$SUUMO_MAKE_QA_BUILD_EXIT";; esac\n')
            python.chmod(0o700)
            docker.chmod(0o700)
            environment = {**os.environ, 'PATH': str(root) + os.pathsep + os.environ['PATH'],
                           'SUUMO_MAKE_QA_LOG': str(log), 'SUUMO_MAKE_QA_BUILD_EXIT': str(build_exit)}
            result = subprocess.run(['make', 'release-publish-deploy', 'host=qa-host', 'tag=qa-retry-01'],
                                    cwd=ROOT, env=environment, text=True, capture_output=True, timeout=20)
            return result.returncode, log.read_text().splitlines()

    def test_build_finishes_before_deploy(self):
        """Even recursive make must publish successfully before attempting deployment."""
        status, order = self.invoke()
        self.assertEqual(status, 0)
        self.assertEqual(order, ['PLAN', 'BUILD', 'DEPLOY'])

    def test_failed_build_never_deploys(self):
        """A failed image publication cannot install a matching-looking stale host bundle."""
        status, order = self.invoke(1)
        self.assertNotEqual(status, 0)
        self.assertEqual(order, ['PLAN', 'BUILD'])


if __name__ == '__main__':
    unittest.main()
