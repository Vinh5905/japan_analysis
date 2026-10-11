"""Durable control state shared by the host bot, VPN hooks and runner."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid


class ControlState:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.transaction() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS values_store (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS confirmations (nonce TEXT PRIMARY KEY, expires REAL NOT NULL, used INTEGER NOT NULL DEFAULT 0)"
            )
        path.chmod(0o600)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def put(db, key, value):
        db.execute(
            "INSERT OR REPLACE INTO values_store VALUES (?, ?)",
            (key, json.dumps(value)),
        )

    @staticmethod
    def read(db, key, default=None):
        row = db.execute(
            "SELECT value FROM values_store WHERE key=?", (key,)
        ).fetchone()
        return json.loads(row[0]) if row else default

    def get(self, key, default=None):
        with self.transaction() as db:
            return self.read(db, key, default)

    def set(self, key, value):
        with self.transaction() as db:
            self.put(db, key, value)

    def accept_update(self, update_id):
        # Persist BEFORE any external side effect. A crash may lose a response,
        # but never replays a start when long polling resumes.
        with self.transaction() as db:
            if update_id < self.read(db, "offset", 0):
                return False
            self.put(db, "offset", update_id + 1)
            return True

    def confirmation(self, now=None, area=None):
        now = time.time() if now is None else now
        nonce = uuid.uuid4().hex
        with self.transaction() as db:
            db.execute("DELETE FROM confirmations WHERE expires < ? OR used=1", (now,))
            # Only the newest prompt can start a run.
            db.execute("UPDATE confirmations SET used=1")
            db.execute("INSERT INTO confirmations VALUES (?, ?, 0)", (nonce, now + 120))
            self.put(db, "confirmation_area", {"nonce": nonce, "area": area})
        return nonce

    def consume_confirmation(self, nonce, now=None):
        now = time.time() if now is None else now
        with self.transaction() as db:
            cursor = db.execute(
                "UPDATE confirmations SET used=1 WHERE nonce=? AND used=0 AND expires>?",
                (nonce, now),
            )
            return cursor.rowcount == 1

    def request_start(self, now=None, area=None, nonce=None):
        """Consume confirmation and enqueue atomically; accepted work has no TTL."""
        now = time.time() if now is None else now
        with self.transaction() as db:
            if nonce:
                selected = self.read(db, "confirmation_area", {})
                cursor = db.execute(
                    "UPDATE confirmations SET used=1 WHERE nonce=? AND used=0 AND expires>?",
                    (nonce, now),
                )
                if cursor.rowcount != 1 or selected.get("nonce") != nonce:
                    return False
                area = selected.get("area")
            pending = self.read(db, "start_request")
            if pending:
                return False
            if not area:
                raise ValueError("Select a ward before confirming")
            self.put(
                db, "start_request", {"at": now, "id": uuid.uuid4().hex, "area": area}
            )
            return True

    def launch(self, area, source, request_id=None, now=None):
        now = time.time() if now is None else now
        run = {
            "pipeline_key": request_id or uuid.uuid4().hex,
            "source": source,
            "area": area,
            "started": now,
            "updated": now,
            "step": "launching",
            "status": "launching",
            "completion": None,
            "cleanup_confirmed": False,
        }
        self.set("pipeline", run)
        return run

    def begin(self, source="schedule", now=None, run_id=None, created_at=None):
        with self.transaction() as db:
            run = self.read(db, "pipeline", {})
            if run.get("status") != "launching" or run_id is None:
                raise RuntimeError("Dispatcher context required before VPN")
            run.update(
                run_id=str(run_id),
                status="running",
                step="vpn_preflight",
                started=created_at,
                updated=time.time(),
            )
            pending = self.read(db, "start_request")
            if pending and pending["id"] == run["pipeline_key"]:
                self.put(db, "start_request", None)
            self.put(db, "pipeline", run)
            return run

    def progress(self, step, **values):
        with self.transaction() as db:
            run = self.read(db, "pipeline", {})
            if run:
                if values.get("status") == "failed":
                    run.setdefault("failure_step", step)
                run.update(values, step=step, updated=time.time())
                self.put(db, "pipeline", run)
            return run


def state_for(env_file: Path):
    return ControlState(
        env_file.resolve().parent / "state" / "telegram-control.sqlite3"
    )


def install_context(run):
    """Install the frozen ward and verified VPN context for all pipeline stages."""
    if run:
        os.environ["TELEGRAM_PIPELINE_RUN_ID"] = str(
            run.get("run_id", run.get("pipeline_key", ""))
        )
        area = run.get("area", {})
        os.environ["SUUMO_RUN_AREA"] = " · ".join(
            str(area[k])
            for k in ("prefecture", "district", "municipality", "ward")
            if area.get(k)
        )
        if run.get("run_id"):
            os.environ["SUUMO_RUN_ID"] = str(run["run_id"])
        if area.get("search_url"):
            os.environ["SUUMO_SEARCH_URL"] = area["search_url"]
        os.environ["SUUMO_HTML_LINKS_FILE"] = (
            "tmp/runs/" + run.get("pipeline_key", str(run.get("run_id"))) + "/links.txt"
        )
        vpn = run.get("vpn") or run.get("vpn_attempt") or {}
        os.environ["SUUMO_VPN_FILENAME"] = str(vpn.get("filename", ""))
        os.environ["SUUMO_VPN_ID"] = str(run.get("vpn", {}).get("vpn_id", ""))
