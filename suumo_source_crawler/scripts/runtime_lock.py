"""Keep deploy and crawler execution from changing a release concurrently."""

from contextlib import contextmanager
from pathlib import Path
import fcntl


@contextmanager
def release_lock(directory: Path):
    """Acquire the shared host lock, failing immediately when already held."""
    with (directory / ".release.lock").open("a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another crawler run or deploy holds the release lock") from exc
        yield
