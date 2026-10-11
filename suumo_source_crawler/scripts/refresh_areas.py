#!/usr/bin/env python3
"""Background catalogue refresh, guarded against parallel refresh processes."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "crawler"))
from scripts.area_catalog import refresh
from scripts.run_release_pipeline import read_env_file
from scripts.telegram_control import Host
from scripts.telegram_state import state_for
from crawler.telegram_notifier import TelegramNotifier, build_event_message
import argparse
import fcntl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--compose-file", type=Path, required=True)
    args = parser.parse_args()
    values = read_env_file(args.env_file)
    state = state_for(args.env_file)
    notifier = TelegramNotifier.from_env(values)
    with (state.path.parent / "area-refresh.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        try:
            result = refresh(Host(args.env_file, args.compose_file, values), force=True)
            notifier.send_message(
                build_event_message(
                    "ĐỒNG BỘ KHU VỰC HOÀN THÀNH",
                    {
                        "Phạm vi": "大阪府 · 大阪市",
                        "Thêm mới": result["added"],
                        "Cập nhật mã": result["updated"],
                        "Giữ nguyên": result["unchanged"],
                    },
                )
            )
        except Exception as exc:
            notifier.send_message(
                build_event_message(
                    "ĐỒNG BỘ KHU VỰC THẤT BẠI",
                    {
                        "Phạm vi": "大阪府 · 大阪市",
                        "Lý do": type(exc).__name__,
                        "Danh mục": "Giữ nguyên lần thành công trước",
                    },
                )
            )
            raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
