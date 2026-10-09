#!/usr/bin/env python3
"""Private Telegram control bot. Standard library only; no webhook or host DB driver."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "crawler"))
from crawler.telegram_notifier import load_telegram_config, sanitize_text, prepare_html
from scripts.run_release_pipeline import read_env_file
from scripts.runtime_lock import release_lock
from scripts.telegram_state import state_for
from scripts import telegram_ui as ui

SERVICE = "suumo-crawler-pipeline.service"
TIMER = "suumo-crawler-pipeline.timer"
BUSY = {"active", "activating", "deactivating", "reloading"}
ZONE = ZoneInfo("Asia/Ho_Chi_Minh")
COMMANDS = [
    ("start", "Mở menu điều khiển"), ("help", "Hướng dẫn và cách đọc số liệu"),
    ("run_crawl", "Chọn ward và xác nhận chạy"), ("areas", "Danh mục ward và lịch sử"),
    ("refresh_areas", "Đồng bộ danh mục SUUMO"), ("status", "Trạng thái crawler và VPN"),
    ("schedule", "Lịch systemd thực tế"), ("history", "5 lượt pipeline gần nhất"),
    ("total", "Tổng URL đã xử lý và lượt crawl"),
]
STEPS = {"vpn_preflight": "🔐 Kiểm tra VPN", "vpn_preflight_failed": "🔴 Kiểm tra VPN thất bại",
         "vpn_ready": "🔐 VPN đã khỏe", "start_postgres_minio": "Khởi động PostgreSQL / MinIO",
         "crawler_init": "Khởi tạo crawler", "suumo-links": "🔎 Tìm links", "suumo-html": "📥 Tải HTML",
         "suumo-page": "🧩 Parse dữ liệu", "awaiting_vpn_cleanup": "Chờ tắt VPN",
         "vpn_cleanup": "🔐 Đang tắt VPN", "vpn_cleanup_failed": "🔴 Tắt VPN thất bại",
         "completed": "🟢 Hoàn thành", "failed": "🔴 Thất bại"}
LOG = logging.getLogger("suumo.telegram.control")


class ApiError(RuntimeError):
    def __init__(self, code, description, retry_after=0):
        super().__init__(description)
        self.code, self.retry_after = code, retry_after


class TelegramApi:
    def __init__(self, token):
        self.token = token

    def call(self, method, payload=None):
        request = Request(f"https://api.telegram.org/bot{self.token}/{method}",
                          data=json.dumps(payload or {}).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=40 if method == "getUpdates" else 10) as response:
                result = json.load(response)
        except HTTPError as exc:
            try:
                result = json.loads(exc.read())
            except (ValueError, OSError):
                raise ApiError(exc.code, "Telegram HTTP error") from None
        if not result.get("ok"):
            raise ApiError(result.get("error_code"), sanitize_text(result.get("description"), self.token),
                           result.get("parameters", {}).get("retry_after", 0))
        return result["result"]


def host_command(command):
    """Run a host command without consuming the caller's SSH upload stream."""
    # Never include raw stderr/config output in Telegram: it can contain secrets.
    environment = dict(os.environ)
    environment.pop("SUUMO_CRAWLER_TAG", None)
    # Compose exec attaches stdin by default even for psql -c; do not let it
    # drain a tar stream that vpn_pool.receive is about to read from SSH stdin.
    result = subprocess.run(command, capture_output=True, text=True, timeout=20, env=environment,
                            stdin=subprocess.DEVNULL)
    if result.returncode:
        raise RuntimeError(f"Host command failed: {command[0]} (exit {result.returncode})")
    return result.stdout.strip()


class Host:
    def __init__(self, env_file, compose_file, values, command=host_command):
        self.env_file, self.compose_file, self.values, self.command = env_file, compose_file, values, command
        self.compose = ["docker", "compose", "--env-file", str(env_file), "-f", str(compose_file)]
        self.source_id = int(values.get("SUUMO_SOURCE_ID", "1"))
        if self.source_id < 1:
            raise ValueError("SUUMO_SOURCE_ID must be positive")

    def properties(self, unit, names):
        output = self.command(["systemctl", "show", unit, "--property=" + ",".join(names)])
        return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)

    def busy(self):
        props = self.properties(SERVICE, ["LoadState", "ActiveState"])
        if props.get("LoadState") != "loaded":
            raise RuntimeError("Crawler systemd unit chưa được cài")
        if props.get("ActiveState") in BUSY:
            return True
        config = json.loads(self.command([*self.compose, "config", "--format", "json"]))
        active = self.command(["docker", "ps", "--filter", "label=com.docker.compose.project=" + config["name"],
                               "--format", '{{.Label "com.docker.compose.service"}}'])
        return bool(set(active.splitlines()) & {"crawler-init", "suumo-links", "suumo-html", "suumo-page", "suumo-tools", "suumo-rerun-html"})

    def start(self):
        self.command(["systemctl", "start", "--no-block", SERVICE])

    def query(self, sql):
        output = self.command([*self.compose, "exec", "-T", "postgres", "psql", "-X", "-q", "-A", "-t",
                               "-v", "ON_ERROR_STOP=1", "-U", self.values.get("POSTGRES_USER", "suumo_user"),
                               "-d", self.values.get("POSTGRES_DB", "suumo_crawler"), "-c", sql])
        return json.loads(output) if output else None

    def history(self):
        # Snapshot association survives parsing/status changes in crawl_tasks.
        return self.query(f"""SELECT COALESCE(json_agg(r ORDER BY created_at DESC, run_id DESC), '[]'::json)
          FROM (SELECT c.run_id, c.created_at, c.finished_at, c.created_by, c.total_urls, c.area_snapshot, c.pipeline_status, c.pipeline_finished_at, c.vpn_snapshot,
          (SELECT count(*) FROM crawl_tasks t WHERE t.run_id=c.run_id AND t.raw_snapshot_id IS NOT NULL) AS html_success,
          (SELECT count(*) FROM crawl_tasks t WHERE t.run_id=c.run_id AND t.raw_snapshot_id IS NULL AND t.status='failed') AS html_failed
          FROM crawl_runs c WHERE source_id={self.source_id}
          ORDER BY created_at DESC, run_id DESC LIMIT 5) r""")

    def total(self):
        return self.query(f"SELECT json_build_object('total_urls', COALESCE(SUM(total_urls), 0), 'runs', COUNT(*)) FROM crawl_runs WHERE source_id={self.source_id}")

    def daily(self, now=None):
        from scripts.crawl_dispatcher import day
        today = day(time.time() if now is None else now)
        return self.query(f"SELECT json_build_object('total_urls',coalesce(sum(total_urls),0),'runs',count(*)) FROM crawl_runs WHERE source_id={self.source_id} AND (created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date='{today}'::date")

    def areas(self, now=None):
        from scripts.crawl_dispatcher import day
        today = day(time.time() if now is None else now)
        return self.query(f"""SELECT coalesce(json_agg(a ORDER BY sc),'[]'::json) FROM (
          SELECT a.*,count(r.run_id) AS runs,max(r.created_at) AS last_run,
           count(r.run_id) FILTER(WHERE (r.created_at AT TIME ZONE 'Asia/Ho_Chi_Minh')::date='{today}'::date) AS today_runs
          FROM crawl_areas a LEFT JOIN crawl_runs r ON r.area_id=a.area_id
          WHERE a.source_id={self.source_id} AND a.prefecture='大阪府' AND a.municipality='大阪市'
          GROUP BY a.area_id) a""")

    def unresolved(self):
        return self.query(f"""SELECT row_to_json(r) FROM (SELECT run_id,pipeline_key,pipeline_status,area_snapshot,vpn_snapshot,created_by,extract(epoch from created_at) AS started FROM crawl_runs
         WHERE source_id={self.source_id} AND pipeline_key IS NOT NULL AND cleanup_confirmed_at IS NULL
         ORDER BY created_at DESC LIMIT 1) r""")

    def vpn_stopped(self):
        from scripts.stop_openvpn import vpn_stopped_reason
        def runner(command):
            try:
                return subprocess.CompletedProcess(command,0,stdout=self.command(list(command)),stderr="")
            except (OSError, RuntimeError, subprocess.SubprocessError):
                return subprocess.CompletedProcess(command,1,stdout="",stderr="")
        from scripts.docker_vpn import DockerVpn, docker_backend
        host_stopped = vpn_stopped_reason("openvpn-client@japan", "tun0", runner)[0]
        return host_stopped and (DockerVpn(self).stopped() if docker_backend(self.values) else True)

    def pipeline_by_key(self, key):
        from scripts.area_catalog import literal
        return self.query(f"""SELECT row_to_json(r) FROM (SELECT run_id,pipeline_status,cleanup_confirmed_at,
          extract(epoch from cleanup_confirmed_at) AS cleanup_epoch FROM crawl_runs
          WHERE source_id={self.source_id} AND pipeline_key={literal(key)}) r""")

    def wake(self):
        from scripts.crawl_dispatcher import wake
        wake(self)

    def schedule(self):
        props = self.properties(TIMER, ["LoadState", "ActiveState", "UnitFileState", "TimersCalendar", "NextElapseUSecRealtime"])
        if props.get("LoadState") != "loaded":
            return {"Lịch": "Timer chưa được cài"}
        enabled = props.get("ActiveState") == "active"
        next_time = props.get("NextElapseUSecRealtime", "")
        # systemctl --value formats this timestamp with the host's timezone.
        # Ask systemd for epoch microseconds via its D-Bus property instead.
        epoch = None
        if enabled and next_time not in {"", "n/a", "0"}:
            path = "/org/freedesktop/systemd1/unit/" + TIMER.replace("_", "_5f").replace("-", "_2d").replace(".", "_2e")
            raw = self.command(["busctl", "get-property", "org.freedesktop.systemd1", path,
                                "org.freedesktop.systemd1.Timer", "NextElapseUSecRealtime"])
            epoch = int(raw.split()[1]) / 1_000_000
        timezone_name = self.command(["timedatectl", "show", "--property=Timezone", "--value"])
        return {"Timer": "đang bật" if enabled else "đã tắt",
                "Tự bật khi boot": props.get("UnitFileState", "unknown"),
                "Lịch thực tế": props.get("TimersCalendar") or "chưa có lịch calendar",
                "Timezone VPS": timezone_name,
                "Lần kế tiếp (giờ Việt Nam)": datetime.fromtimestamp(epoch, ZONE).isoformat(timespec="seconds") if epoch else "chưa có",
                "Còn lại": f"{max(0, int(epoch - time.time())) // 60} phút" if epoch else "chưa có"}

    def status(self, state):
        busy = self.busy()
        props = self.properties(SERVICE, ["ActiveState", "SubState", "Result"])
        run = state.get("pipeline", {})
        vpn = self.properties("openvpn-client@japan", ["ActiveState"])
        from scripts.ensure_openvpn import vpn_health_reason
        def runner(command):
            if tuple(command[:2]) == ("systemctl", "is-active"):
                # Inactive is a valid state with a nonzero CLI exit code.
                return subprocess.CompletedProcess(command, 0, stdout=vpn.get("ActiveState", "unknown"), stderr="")
            try:
                return subprocess.CompletedProcess(command, 0, stdout=self.command(list(command)), stderr="")
            except RuntimeError:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        from scripts.docker_vpn import DockerVpn, docker_backend
        if docker_backend(self.values):
            healthy, reason = DockerVpn(self).health()
            vpn = {'ActiveState': 'Docker'}
        else:
            healthy, reason = vpn_health_reason("openvpn-client@japan", "tun0", runner)
        return {"Crawler": "đang chạy" if busy else "rảnh", "Systemd": f"{props.get('ActiveState')} / {props.get('SubState')}",
                "Bước hiện tại" if busy else "Bước gần nhất": STEPS.get(run.get("step"), run.get("step", "chưa có")),
                "Lượt chạy": run.get("run_id", "chưa có"), "Kết quả gần nhất": props.get("Result", "unknown"),
                "VPN": "khỏe (Docker tunnel + firewall)" if healthy and docker_backend(self.values) else "khỏe (tun0 + route)" if healthy else f"{vpn.get('ActiveState', 'unknown')} · {reason}",
                "Cấu hình VPN": (run.get('vpn') or run.get('vpn_attempt') or {}).get('filename', 'chưa có'),
                "Khu vực": run.get("area", {}).get("display_name", "chưa có")}


class Controller:
    def __init__(self, api, state, host, owner):
        self.api, self.state, self.host, self.owner = api, state, host, str(owner)
        if not self.owner.isdigit() or int(self.owner) <= 0:
            raise ValueError("TELEGRAM_CHAT_ID must be the positive owner ID of a private chat")

    def safe_call(self, method, payload):
        try:
            return self.api.call(method, payload)
        except Exception as exc:
            LOG.warning("Telegram reply failed: %s", type(exc).__name__)

    def present(self, card, message_id=None):
        # Both commands and callbacks use the same bounded, redacted HTML cards.
        config = load_telegram_config(self.host.values)
        message, markup = card
        payload = {"chat_id": self.owner, "text": prepare_html(message, config),
                   "parse_mode": "HTML", "reply_markup": markup}
        if message_id is not None:
            try:
                return self.api.call("editMessageText", {**payload, "message_id": message_id})
            except ApiError as exc:
                if exc.code == 400 and "message is not modified" in str(exc).lower():
                    return
                LOG.warning("Telegram edit failed: code %s", exc.code)
            except Exception as exc:
                LOG.warning("Telegram edit failed: %s", type(exc).__name__)
            # Old/deleted menu messages can still yield a fresh response.
        return self.safe_call("sendMessage", payload)

    def view(self, name, now, message_id=None):
        if name == "home":
            card = ui.home(now)
        elif name == "help":
            card = ui.help_card(COMMANDS, now)
        elif name in {"run_crawl", "areas"}:
            card = ui.areas(self.host.areas(now), name == "run_crawl", 0, now)
        elif name == "refresh_areas":
            unit = "suumo-crawler-refresh-areas.service"
            props = self.host.properties(unit, ["ActiveState"])
            if props.get("ActiveState") in BUSY:
                description = "Đang đồng bộ danh mục SUUMO; kết quả sẽ được gửi khi hoàn tất."
            else:
                self.host.command(["systemctl", "start", "--no-block", unit])
                description = "Đã tiếp nhận đồng bộ nền. Bot sẽ báo số ward thêm mới / cập nhật / giữ nguyên."
            card = ui.notice("↻ SUUMO · Đồng bộ khu vực", description, now, "areas")
        elif name == "status":
            card = ui.status(self.run_status(now), now)
        elif name == "schedule":
            card = ui.schedule(self.effective_schedule(now), now)
        elif name == "history":
            card = ui.history(self.host.history(), self.host.source_id, now)
        elif name == "total":
            card = ui.total({**self.host.total(), "today": self.host.daily(now)}, self.host.source_id, now)
        else:
            raise ValueError("Unknown controller view")
        self.present(card, message_id)

    def authorized(self, message, sender):
        chat = message.get("chat", {})
        return (chat.get("type") == "private" and str(chat.get("id")) == self.owner
                and str(sender.get("id")) == self.owner and not sender.get("is_bot", False))

    def handle(self, update, now=None):
        now = time.time() if now is None else now
        if not self.state.accept_update(update["update_id"]):
            return
        callback = update.get("callback_query")
        message = (callback or {}).get("message") or update.get("message", {})
        sender = (callback or message).get("from", {})
        if not self.authorized(message, sender):
            return
        try:
            if callback:
                self.callback(callback, now)
                return
            command = message.get("text", "").split(" ", 1)[0]
            name = command.removeprefix("/")
            if command == "/run_crawl" and (now - message.get("date", 0) > 300 or message.get("date", 0) > now + 30):
                self.present(ui.notice("⏳ SUUMO · Yêu cầu đã cũ", "Gửi lại /run_crawl; lệnh quá 5 phút không được sử dụng.", now))
            elif command.startswith("/") and name in ui.VIEWS | {"start"}:
                self.view("home" if name == "start" else name, now)
            else:
                self.present(ui.notice("❔ SUUMO · Chọn chức năng", "Bấm Menu bên dưới hoặc gửi /help để xem các lệnh.", now, "help"))
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            LOG.error("Control command failed: %s: %s", type(exc).__name__, sanitize_text(exc))
            running_action = callback and callback.get("data", "").startswith("run:")
            title = "🟠 SUUMO · Chưa xác định kết quả chạy" if running_action else "🟠 SUUMO · Chưa lấy được dữ liệu"
            description = ("Kiểm tra Trạng thái trước khi gửi yêu cầu chạy mới. Chi tiết được ghi trong log VPS." if running_action
                           else "VPS chưa trả được dữ liệu. Bấm Cập nhật để thử lại sau. Chi tiết được ghi trong log VPS.")
            self.present(ui.notice(title, description, now),
                         message.get("message_id") if callback else None)

    def pending(self, now):
        return bool(self.state.get("start_request"))

    def effective_schedule(self, now):
        from scripts.crawl_dispatcher import decision
        fields = self.host.schedule()
        reason, next_at = decision(self.state, self.host.daily(now), now)
        run = self.state.get("pipeline", {})
        pending = self.state.get("start_request")
        if self.host.busy():
            reason, next_at = "Chờ lượt hiện tại hoàn tất cleanup", None
        elif self.host.unresolved():
            reason, next_at = "Cleanup chưa được xác nhận; chặn lượt tiếp theo", None
        elif pending:
            reason, next_at = "Ưu tiên ward đang chờ: " + pending["area"]["display_name"], now
        if fields.get("Timer") != "đang bật" and not pending:
            reason, next_at = "Timer đang tắt", None
        fields["Điều phối"] = reason
        fields["Lần kế tiếp (giờ Việt Nam)"] = datetime.fromtimestamp(next_at, ZONE).isoformat() if next_at else "chưa có"
        fields["Còn lại"] = f"{max(0,int(next_at-now))//60} phút" if next_at else "chờ điều kiện"
        return fields

    def run_status(self, now):
        fields = self.host.status(self.state)
        run = self.state.get("pipeline", {})
        fields["Khu vực"] = run.get("area", {}).get("display_name", "chưa có")
        pending = self.state.get("start_request")
        if pending:
            fields["Yêu cầu Telegram"] = pending["area"]["display_name"] + " · sẽ chạy sau cleanup"
        schedule = self.effective_schedule(now)
        fields["Lịch"] = schedule["Điều phối"]
        fields["Lần kế tiếp"] = schedule["Lần kế tiếp (giờ Việt Nam)"]
        daily = self.host.daily(now)
        fields["Hôm nay"] = f"{ui.number(daily['total_urls'])} / 10.000 URL · {daily['runs']} / 5 lượt"
        return fields

    def callback(self, callback, now):
        action, _, nonce = callback.get("data", "").partition(":")
        if action == "view" and nonce in ui.VIEWS:
            self.safe_call("answerCallbackQuery", {"callback_query_id": callback["id"]})
            self.view(nonce, now, callback["message"]["message_id"])
            return
        if action in {"page", "pick"}:
            self.safe_call("answerCallbackQuery", {"callback_query_id": callback["id"]})
            if action == "page":
                mode, page = nonce.split(":")
                self.present(ui.areas(self.host.areas(now), mode == "run", int(page), now), callback["message"]["message_id"])
            else:
                areas = self.host.areas(now)
                area = next((a for a in areas if a["area_id"] == int(nonce)), None)
                if not area:
                    raise ValueError("Ward unavailable")
                token = self.state.confirmation(now, area)
                self.present(ui.area_confirmation(area, self.host.values, token, now,
                            self.state.get("start_request"), self.state.get("pipeline")), callback["message"]["message_id"])
            return
        # Respond immediately before SQLite/DB/systemd work.
        self.safe_call("answerCallbackQuery", {"callback_query_id": callback["id"]})
        if action == "cancel":
            accepted = self.state.consume_confirmation(nonce, now)
        elif action == "run":
            accepted = self.state.request_start(now, nonce=nonce)
        else:
            accepted = False
        if not accepted:
            pending = self.state.get("start_request")
            description = ("Đã có ward đang chờ: " + ui.text(pending["area"]["display_name"]) + ". Không thay thế yêu cầu này."
                           if pending else "Xác nhận hết hạn hoặc đã sử dụng. Chọn ward để tạo xác nhận mới.")
            self.present(ui.notice("⏳ SUUMO · Yêu cầu", description, now), callback["message"]["message_id"])
            return
        if action == "cancel":
            self.present(ui.notice("⚪ SUUMO · Đã hủy yêu cầu", "Chưa tạo yêu cầu crawl.", now, "home"), callback["message"]["message_id"])
            return
        pending = self.state.get("start_request")
        # Queue is durable before wake; a failed wake is recovered by the minute timer.
        self.host.wake()
        running = self.state.get("pipeline", {}).get("area", {}).get("display_name", "chưa có")
        self.present(ui.notice("🔵 SUUMO · Đã nhận yêu cầu", "Ward sẽ chạy: <b>" + ui.text(pending["area"]["display_name"]) +
                     "</b>\nLượt hiện tại/gần nhất: " + ui.text(running) +
                     "\nYêu cầu được giữ qua restart và không hết hạn. Lượt tiếp theo chỉ bắt đầu khi cleanup xác nhận VPN đã tắt.", now), callback["message"]["message_id"])



def poll(controller, sleeper=time.sleep, stop=lambda: False):
    ready, delay = False, 1
    while not stop():
        try:
            if not ready:
                if controller.api.call("getWebhookInfo").get("url"):
                    raise ApiError(409, "Token đang có webhook; bot từ chối polling và không xóa webhook.")
                controller.api.call("setMyCommands", {"commands": [{"command": key, "description": description} for key, description in COMMANDS],
                                                      "scope": {"type": "chat", "chat_id": controller.owner}})
                ready = True
            updates = controller.api.call("getUpdates", {"offset": controller.state.get("offset", 0), "timeout": 25,
                                                          "allowed_updates": ["message", "callback_query"]})
            for update in updates:
                controller.handle(update)
            delay = 1
        except ApiError as exc:
            LOG.warning("Telegram API failure: code %s", exc.code)
            if exc.code in {401, 409}:
                raise
            sleeper(min(59, max(delay, exc.retry_after)) + random.uniform(0, 0.5))
            delay = min(delay * 2, 60)
        except (OSError, ValueError, RuntimeError) as exc:
            LOG.warning("Polling reconnect: %s", type(exc).__name__)
            sleeper(min(delay, 59) + random.uniform(0, 0.5))
            delay = min(delay * 2, 60)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=ROOT.parent / ".env")
    parser.add_argument("--compose-file", type=Path, default=ROOT.parent / "docker-compose.release.yml")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    values = read_env_file(args.env_file)
    if values.get("TELEGRAM_CONTROL_ENABLED", "false").lower() != "true":
        LOG.info("Telegram control disabled")
        return 0
    config = load_telegram_config(values)
    if not config.enabled:
        raise ValueError("Telegram control requires token and private chat ID")
    # A separate lifetime lock prevents two local bot processes sharing offsets.
    import fcntl
    state = state_for(args.env_file)
    with (state.path.parent / "telegram-bot.lock").open("a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        poll(Controller(TelegramApi(config.bot_token), state,
                        Host(args.env_file.resolve(), args.compose_file.resolve(), values), config.chat_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
