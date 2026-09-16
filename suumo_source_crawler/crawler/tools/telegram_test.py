from __future__ import annotations

import argparse

from crawler.telegram_notifier import (
    TelegramNotifier,
    build_event_message,
    current_timestamp,
    machine_name,
)


def parse_args() -> argparse.Namespace:
    """Parse an optional label for the Telegram connectivity test."""

    parser = argparse.ArgumentParser(description="Send one SUUMO Telegram test message.")
    parser.add_argument(
        "--message",
        default="Kết nối Telegram Bot API hoạt động.",
        help="Short text included in the test notification.",
    )
    return parser.parse_args()


def main() -> int:
    """Send a test message and return a useful CLI status code."""

    args = parse_args()
    notifier = TelegramNotifier.from_env()
    message = build_event_message(
        "KIỂM TRA TELEGRAM",
        {
            "Ứng dụng": "suumo_source_crawler",
            "Nội dung": args.message,
            "Host": machine_name(),
            "Thời gian": current_timestamp(),
        },
    )
    result = notifier.send_message(message)
    if result.sent:
        print("Telegram test notification sent successfully")
        return 0

    print(f"Telegram test failed: {result.error_type}: {result.error_message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
