from __future__ import annotations

import json
import logging
import os
import re
import socket
import time
from html import escape, unescape
from html.parser import HTMLParser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOGGER = logging.getLogger("crawler.telegram")
TELEGRAM_MESSAGE_LIMIT = 4096
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_SEND_RETRIES = 3
MAX_RATE_LIMIT_WAIT_SECONDS = 30


@dataclass(frozen=True)
class TelegramConfig:
    """Store Telegram Bot API configuration loaded from environment variables."""

    bot_token: str = field(repr=False)
    chat_id: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    secrets: tuple[str, ...] = field(default=(), repr=False)

    @property
    def enabled(self) -> bool:
        """Return true only when both required Telegram values are present."""

        return bool(self.bot_token and self.chat_id)


@dataclass(frozen=True)
class TelegramSendResult:
    """Describe a notification attempt without raising into crawler code."""

    configured: bool
    sent: bool
    status_code: int | None = None
    error_type: str | None = None
    error_message: str | None = None


def load_telegram_config(
    environ: Mapping[str, str] | None = None,
) -> TelegramConfig:
    """Load Telegram credentials without providing unsafe source-code defaults."""

    values = os.environ if environ is None else environ
    return TelegramConfig(
        bot_token=str(values.get("TELEGRAM_BOT_TOKEN", "")).strip(),
        chat_id=str(values.get("TELEGRAM_CHAT_ID", "")).strip(),
        secrets=tuple(
            str(value)
            for key, value in values.items()
            if value and re.search(r"(?i)(password|passwd|secret|token|api_key)$", key)
        ),
    )


def current_timestamp(environ: Mapping[str, str] | None = None) -> str:
    """Return Telegram timestamps in Vietnam time, independent of host TZ."""

    timezone_name = "Asia/Ho_Chi_Minh"
    try:
        local_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        local_timezone = timezone.utc
    return datetime.now(local_timezone).isoformat(timespec="seconds")


def machine_name(environ: Mapping[str, str] | None = None) -> str:
    """Return the VPS hostname propagated by the runner or the current hostname."""

    values = os.environ if environ is None else environ
    return str(values.get("TELEGRAM_HOSTNAME", "")).strip() or socket.gethostname()


def sanitize_text(value: object, bot_token: str = "", strip: bool = True) -> str:
    """Remove control characters and redact a bot token from notification text."""

    text = str(value if value is not None else "").replace("\x00", "")
    if strip:
        text = text.strip()
    if bot_token:
        text = text.replace(bot_token, "[REDACTED_TELEGRAM_TOKEN]")
    text = re.sub(r"/bot\d+:[A-Za-z0-9_-]+/", "/bot[REDACTED]/", text)
    text = re.sub(r"\b\d{5,}:[A-Za-z0-9_-]{10,}\b", "[REDACTED_TOKEN]", text)
    text = re.sub(
        r"(?i)(password|passwd|secret|token|api_key)(\s*[=:]\s*)[^\s,;]+",
        r"\1\2[REDACTED]",
        text,
    )
    text = re.sub(r"(://[^\s/:]+:)[^\s/@]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def prepare_html(message: str, config: TelegramConfig) -> str:
    """Redact decoded text nodes, keeping generated tags and entities intact."""

    class Redactor(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []

        def handle_starttag(self, tag, attrs):
            self.parts.append(
                "<b>" if tag == "b" and not attrs else escape(self.get_starttag_text())
            )

        def handle_endtag(self, tag):
            self.parts.append("</b>" if tag == "b" else escape(f"</{tag}>"))

        def handle_data(self, data):
            # Replace known secrets before applying patterns so markup cannot be
            # damaged by short secrets or by a credential containing < or &.
            for secret in config.secrets:
                data = data.replace(secret, "[REDACTED]")
            self.parts.append(
                escape(sanitize_text(data, config.bot_token, strip=False))
            )

    redactor = Redactor()
    redactor.feed(message)
    redactor.close()
    return truncate_message("".join(redactor.parts))


def message_size(message: str) -> int:
    return len(message.encode("utf-16-le")) // 2


def truncate_message(message: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> str:
    """Keep Telegram messages below the Bot API text limit."""

    if message_size(message) <= limit:
        return message
    suffix = "\n...[đã rút gọn]"
    # Never cut a tag/entity in HTML. Oversized external text becomes escaped
    # plain text; messages built below already fit without losing formatting.
    plain = unescape(re.sub(r"<[^>]*>", "", message))
    while message_size(escape(plain) + suffix) > limit:
        plain = plain[
            : max(
                0, len(plain) - max(1, (message_size(escape(plain) + suffix) - limit))
            )
        ]
    return escape(plain) + suffix


def build_event_message(
    title: str,
    fields: Mapping[str, object],
    possible_causes: list[str] | None = None,
    bot_token: str = "",
    secrets: tuple[str, ...] = (),
) -> str:
    """Escape dynamic text before adding markup; bound each field before escape."""
    upper = title.upper()
    failed = any(word in upper for word in ("THẤT BẠI", "KHÔNG THỂ", "KHÔNG XÁC NHẬN"))
    warning = any(word in upper for word in ("CẢNH BÁO", "CHƯA BẬT", "KHÔNG ỔN ĐỊNH"))
    done = any(word in upper for word in ("HOÀN THÀNH", "ĐÃ BẬT", "ĐÃ TẮT"))
    status = "🔴" if failed else "🟠" if warning else "🟢" if done else "🔵"
    values = {"Giờ Việt Nam": current_timestamp(), **fields}
    job = str(values.get("Job", values.get("Bước lỗi", "")))
    step = (
        "🔐 VPN"
        if "VPN" in upper
        else {
            "suumo_links": "🔎 Tìm links",
            "suumo_html": "📥 Tải HTML",
            "suumo_page": "🧩 Parse dữ liệu",
        }.get(job.replace("-", "_"), "")
    )
    run_id = os.environ.get("TELEGRAM_PIPELINE_RUN_ID", "")
    if run_id:
        values = {"Lượt chạy": run_id[:12], **values}
    if os.environ.get("SUUMO_RUN_AREA"):
        values = {"Khu vực": os.environ["SUUMO_RUN_AREA"], **values}
    if os.environ.get("SUUMO_VPN_FILENAME"):
        values = {"VPN": os.environ["SUUMO_VPN_FILENAME"], **values}
    known_secrets = secrets + load_telegram_config().secrets

    def clean(value, size):
        text = sanitize_text(value, bot_token)
        for secret in known_secrets:
            text = text.replace(secret, "[REDACTED]")
        return escape(text[:size])

    lines = [f"{status} <b>SUUMO · {clean(title, 120)}</b>"]
    if step:
        lines.append(step)
    lines.append("")
    for label, value in values.items():
        if value is None or value == "":
            continue
        size = (
            240
            if any(word in label.lower() for word in ("error", "lỗi", "lý do"))
            else 500
        )
        line = f"{clean(label, 60)}: {clean(value, size)}"
        if message_size("\n".join(lines)) + message_size(line) > 3500:
            lines.append("… Chi tiết trong journald.")
            break
        lines.append(line)

    causes = [clean(cause, 180) for cause in (possible_causes or [])[:2] if cause]
    if causes:
        for cause in causes:
            if message_size("\n".join(lines)) + message_size(cause) + 30 < 3900:
                lines.append(f"💡 {cause}")

    return truncate_message("\n".join(lines))


def infer_possible_causes(text: str) -> list[str]:
    """Infer cautious troubleshooting hints from an error or crawler log excerpt."""

    normalized = text.lower()
    causes: list[str] = []

    if any(
        marker in normalized
        for marker in (
            "dnslookuperror",
            "name or service not known",
            "temporary failure in name resolution",
            "nodename nor servname",
            "lookup registry-1.docker.io",
        )
    ):
        causes.append(
            "DNS không phân giải được; kiểm tra DNS và route sau khi bật VPN."
        )

    if any(
        marker in normalized
        for marker in (
            "timed out",
            "timeout",
            "tcpconnecterror",
            "connection reset",
            "network is unreachable",
        )
    ):
        causes.append(
            "Kết nối mạng hoặc VPN không ổn định, bị timeout hoặc mất route outbound."
        )

    if any(
        marker in normalized
        for marker in (
            "http 403",
            "status 403",
            "forbidden",
            "response_status_count/403",
        )
    ):
        causes.append("SUUMO có thể đang từ chối IP, User-Agent hoặc request hiện tại.")

    if any(
        marker in normalized
        for marker in (
            "http 429",
            "status 429",
            "too many requests",
            "response_status_count/429",
        )
    ):
        causes.append("SUUMO có thể đang rate-limit do số request hoặc tần suất crawl.")

    if "connection refused" in normalized:
        causes.append(
            "Dịch vụ đích chưa sẵn sàng hoặc port/firewall đang từ chối kết nối."
        )

    if any(marker in normalized for marker in ("no such image", "pull access denied")):
        causes.append(
            "Docker image chưa có ở local hoặc image/tag hiện tại không truy cập được."
        )

    return list(dict.fromkeys(causes))


class TelegramNotifier:
    """Send fail-open Telegram notifications through the Bot API."""

    def __init__(self, config: TelegramConfig):
        self.config = config

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> TelegramNotifier:
        """Create a notifier from the two supported Telegram environment variables."""

        return cls(load_telegram_config(environ))

    def send_message(self, message: str) -> TelegramSendResult:
        """Retry transient failures three times, stopping immediately after delivery."""

        if not self.config.enabled:
            return TelegramSendResult(
                configured=False,
                sent=False,
                error_type="TelegramNotConfigured",
                error_message="TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID chưa được cấu hình",
            )

        attempts = 1 + MAX_SEND_RETRIES
        for attempt in range(1, attempts + 1):
            result, retry_after = self._send_once(message)
            if result.sent:
                if attempt > 1:
                    LOGGER.info(
                        "Telegram notification delivered on attempt %s/%s",
                        attempt,
                        attempts,
                    )
                return result
            if retry_after is None or attempt == attempts:
                LOGGER.warning(
                    "Telegram notification not delivered after %s/%s attempts (%s); crawler continues",
                    attempt,
                    attempts,
                    result.error_type,
                )
                return result
            # Give TLS/DNS a chance to recover; respect Telegram's rate-limit wait.
            delay = max(2**attempt, retry_after)
            LOGGER.warning(
                "Telegram notification attempt %s/%s failed (%s); retrying in %s seconds",
                attempt,
                attempts,
                result.error_type,
                delay,
            )
            time.sleep(delay)
        return result

    @staticmethod
    def _retry_delay(status_code: int, body: Mapping[str, object]) -> float | None:
        """Retry server/rate-limit failures without waiting indefinitely or retrying too early."""
        if status_code == 429:
            parameters = body.get("parameters")
            value = (
                parameters.get("retry_after", 0) if isinstance(parameters, dict) else 0
            )
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                return None
            if value > MAX_RATE_LIMIT_WAIT_SECONDS:
                LOGGER.warning(
                    "Telegram retry_after exceeds the bounded notification wait; no early retry"
                )
                return None
            return float(value)
        return 0.0 if 500 <= status_code <= 599 else None

    def _send_once(self, message: str) -> tuple[TelegramSendResult, float | None]:
        """Return one sanitized delivery result and a wait hint for transient failures."""
        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = json.dumps(
                {
                    "chat_id": self.config.chat_id,
                    "text": prepare_html(message, self.config),
                    "parse_mode": "HTML",
                },
                ensure_ascii=False,
            ).encode("utf-8")
            request = Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                status_code = int(response.getcode())
                response_body = response.read()
            parsed_body = (
                json.loads(response_body.decode("utf-8")) if response_body else {}
            )
            if not 200 <= status_code < 300 or parsed_body.get("ok") is False:
                description = sanitize_text(
                    parsed_body.get(
                        "description", "Telegram API trả về kết quả không thành công"
                    ),
                    self.config.bot_token,
                )
                LOGGER.warning("Telegram notification was rejected: %s", description)
                error_code = parsed_body.get("error_code", status_code)
                if not isinstance(error_code, int):
                    error_code = status_code
                return TelegramSendResult(
                    configured=True,
                    sent=False,
                    status_code=error_code,
                    error_type="TelegramApiError",
                    error_message=description,
                ), self._retry_delay(error_code, parsed_body)

            return TelegramSendResult(
                configured=True,
                sent=True,
                status_code=status_code,
            ), None
        except HTTPError as exc:
            error_message = sanitize_text(exc.reason, self.config.bot_token)
            LOGGER.warning("Telegram HTTP request failed: HTTP %s", exc.code)
            body = {}
            if exc.code == 429:
                try:
                    body = json.loads(exc.read().decode("utf-8"))
                    if not isinstance(body, dict):
                        body = {}
                except (OSError, ValueError):
                    pass
            exc.close()
            return TelegramSendResult(
                configured=True,
                sent=False,
                status_code=exc.code,
                error_type=type(exc).__name__,
                error_message=error_message,
            ), self._retry_delay(exc.code, body)
        except Exception as exc:  # noqa: BLE001 - notifications must never stop the crawler.
            error_message = sanitize_text(exc, self.config.bot_token)
            LOGGER.warning(
                "Telegram notification failed without affecting the crawler: %s: %s",
                type(exc).__name__,
                error_message,
            )
            return TelegramSendResult(
                configured=True,
                sent=False,
                error_type=type(exc).__name__,
                error_message=error_message,
            ), 0.0 if isinstance(
                exc, (URLError, OSError, json.JSONDecodeError)
            ) else None
