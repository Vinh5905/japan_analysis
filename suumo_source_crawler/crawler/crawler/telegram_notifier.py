from __future__ import annotations

import json
import logging
import os
import re
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOGGER = logging.getLogger("crawler.telegram")
TELEGRAM_MESSAGE_LIMIT = 4096
DEFAULT_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True)
class TelegramConfig:
    """Store Telegram Bot API configuration loaded from environment variables."""

    bot_token: str = field(repr=False)
    chat_id: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

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
    )


def current_timestamp(environ: Mapping[str, str] | None = None) -> str:
    """Return an ISO timestamp in the configured runtime timezone."""

    values = os.environ if environ is None else environ
    timezone_name = str(values.get("TZ", "Asia/Ho_Chi_Minh")).strip()
    try:
        local_timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        local_timezone = timezone.utc
    return datetime.now(local_timezone).isoformat(timespec="seconds")


def machine_name(environ: Mapping[str, str] | None = None) -> str:
    """Return the VPS hostname propagated by the runner or the current hostname."""

    values = os.environ if environ is None else environ
    return str(values.get("TELEGRAM_HOSTNAME", "")).strip() or socket.gethostname()


def sanitize_text(value: object, bot_token: str = "") -> str:
    """Remove control characters and redact a bot token from notification text."""

    text = str(value or "").replace("\x00", "").strip()
    if bot_token:
        text = text.replace(bot_token, "[REDACTED_TELEGRAM_TOKEN]")
    text = re.sub(r"/bot\d+:[A-Za-z0-9_-]+/", "/bot[REDACTED]/", text)
    return text


def truncate_message(message: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> str:
    """Keep Telegram messages below the Bot API text limit."""

    if len(message) <= limit:
        return message
    suffix = "\n...[đã rút gọn]"
    return f"{message[: limit - len(suffix)]}{suffix}"


def build_event_message(
    title: str,
    fields: Mapping[str, object],
    possible_causes: list[str] | None = None,
    bot_token: str = "",
) -> str:
    """Build a consistent plain-text lifecycle or failure message."""

    lines = [f"[SUUMO] {sanitize_text(title, bot_token)}"]
    for label, value in fields.items():
        if value is None or value == "":
            continue
        lines.append(f"{label}: {sanitize_text(value, bot_token)}")

    causes = [sanitize_text(cause, bot_token) for cause in possible_causes or [] if cause]
    if causes:
        lines.append("Khả năng cần kiểm tra:")
        lines.extend(f"- {cause}" for cause in causes)

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
        causes.append("DNS không phân giải được; kiểm tra DNS và route sau khi bật VPN.")

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
        causes.append("Kết nối mạng hoặc VPN không ổn định, bị timeout hoặc mất route outbound.")

    if any(
        marker in normalized
        for marker in ("http 403", "status 403", "forbidden", "response_status_count/403")
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
        causes.append("Dịch vụ đích chưa sẵn sàng hoặc port/firewall đang từ chối kết nối.")

    if any(marker in normalized for marker in ("no such image", "pull access denied")):
        causes.append("Docker image chưa có ở local hoặc image/tag hiện tại không truy cập được.")

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
        """Send one plain-text message and convert all transport errors into a result."""

        if not self.config.enabled:
            return TelegramSendResult(
                configured=False,
                sent=False,
                error_type="TelegramNotConfigured",
                error_message="TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID chưa được cấu hình",
            )

        try:
            url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
            payload = json.dumps(
                {
                    "chat_id": self.config.chat_id,
                    "text": truncate_message(sanitize_text(message, self.config.bot_token)),
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
            parsed_body = json.loads(response_body.decode("utf-8")) if response_body else {}
            if not 200 <= status_code < 300 or parsed_body.get("ok") is False:
                description = sanitize_text(
                    parsed_body.get("description", "Telegram API trả về kết quả không thành công"),
                    self.config.bot_token,
                )
                LOGGER.warning("Telegram notification was rejected: %s", description)
                return TelegramSendResult(
                    configured=True,
                    sent=False,
                    status_code=status_code,
                    error_type="TelegramApiError",
                    error_message=description,
                )

            return TelegramSendResult(
                configured=True,
                sent=True,
                status_code=status_code,
            )
        except HTTPError as exc:
            error_message = sanitize_text(exc.reason, self.config.bot_token)
            LOGGER.warning("Telegram HTTP request failed: HTTP %s", exc.code)
            return TelegramSendResult(
                configured=True,
                sent=False,
                status_code=exc.code,
                error_type=type(exc).__name__,
                error_message=error_message,
            )
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
            )
