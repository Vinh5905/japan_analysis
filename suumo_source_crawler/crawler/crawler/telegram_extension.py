from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Mapping

from scrapy import signals

from crawler.telegram_notifier import (
    TelegramNotifier,
    build_event_message,
    current_timestamp,
    infer_possible_causes,
    machine_name,
    sanitize_text,
)


LOGGER = logging.getLogger(__name__)
SUCCESS_CLOSE_REASONS = {"finished"}


class TelegramErrorBufferHandler(logging.Handler):
    """Keep ERROR/CRITICAL context for one final job-failure notification."""

    def __init__(self, max_records: int = 20):
        super().__init__(level=logging.ERROR)
        self.max_records = max_records
        self.records: list[dict[str, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Buffer a sanitized error instead of sending every log line to Telegram."""

        if record.name.startswith("crawler.telegram"):
            return

        try:
            error_type = "LoggingError"
            if record.exc_info and record.exc_info[0] is not None:
                error_type = record.exc_info[0].__name__
            elif record.levelno >= logging.CRITICAL:
                error_type = "CriticalLog"

            self.records.append(
                {
                    "error_type": error_type,
                    "error_message": sanitize_text(record.getMessage()),
                }
            )
            if len(self.records) > self.max_records:
                del self.records[: len(self.records) - self.max_records]
        except Exception:
            self.handleError(record)

    @property
    def latest(self) -> dict[str, str] | None:
        """Return the newest buffered error context, if any."""

        return self.records[-1] if self.records else None


@dataclass
class SpiderRunSummary:
    """Store compact lifecycle and crawl-count information for one spider."""

    job_name: str
    status: str
    close_reason: str
    started_at: str
    finished_at: str
    duration_seconds: float
    request_count: int = 0
    response_count: int = 0
    new_links: int = 0
    html_success_count: int = 0
    html_failed_count: int = 0
    parsed_record_count: int = 0
    valid_record_count: int = 0
    invalid_record_count: int = 0
    batch_count: int = 0
    spider_error_count: int = 0
    warning_message: str | None = None
    exception_type: str | None = None
    error_message: str | None = None
    possible_causes: list[str] = field(default_factory=list)


class TelegramNotificationExtension:
    """Report Scrapy lifecycle events and compact job summaries to Telegram."""

    def __init__(self, crawler):
        self.crawler = crawler
        self.notifier = TelegramNotifier.from_env()
        self.started_monotonic: float | None = None
        self.started_at: str | None = None
        self.active_spider_name: str | None = None
        self.closed = False
        self.html_success_count = 0
        self.html_failed_count = 0
        self.parsed_record_count = 0
        self.valid_record_count = 0
        self.invalid_record_count = 0
        self.batch_count = 0
        self.spider_errors: list[dict[str, str]] = []
        self.error_handler = TelegramErrorBufferHandler()
        logging.getLogger().addHandler(self.error_handler)

    @classmethod
    def from_crawler(cls, crawler):
        """Create the extension and subscribe to Scrapy lifecycle signals."""

        extension = cls(crawler)
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(extension.spider_error, signal=signals.spider_error)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(extension.engine_stopped, signal=signals.engine_stopped)
        return extension

    def spider_opened(self, spider) -> None:
        """Send the explicit job-started lifecycle event."""

        self.started_monotonic = time.monotonic()
        self.started_at = current_timestamp()
        self.active_spider_name = spider.name
        message = build_event_message(
            "JOB BẮT ĐẦU",
            {
                "Job": spider.name,
                "Host": machine_name(),
                "Thời gian": self.started_at,
            },
        )
        self.notifier.send_message(message)

    def item_scraped(self, item, response, spider) -> None:
        """Count persisted HTML results and parser batch summaries without changing items."""

        item_data: Mapping[str, object]
        try:
            item_data = dict(item)
        except (TypeError, ValueError):
            return

        if spider.name == "suumo_html":
            if item_data.get("status") == "failed":
                self.html_failed_count += 1
            else:
                self.html_success_count += 1
        elif spider.name == "suumo_page" and "row_count" in item_data:
            self.batch_count += 1
            self.parsed_record_count += int(item_data.get("row_count") or 0)
            self.valid_record_count += int(item_data.get("valid_count") or 0)
            self.invalid_record_count += int(item_data.get("invalid_count") or 0)

    def spider_error(self, failure, response, spider) -> None:
        """Capture unhandled spider callback errors for the final lifecycle summary."""

        exception_type = getattr(getattr(failure, "type", None), "__name__", "SpiderError")
        error_message = sanitize_text(getattr(failure, "value", failure))
        self.spider_errors.append(
            {
                "error_type": exception_type,
                "error_message": error_message,
            }
        )

    def spider_closed(self, spider, reason: str) -> None:
        """Send one completion, warning, or failure message and persist its summary."""

        summary = self._build_summary(spider, reason)
        self._write_summary(summary)
        self._send_summary(summary)
        self.closed = True
        self._remove_error_handler()

    def engine_stopped(self) -> None:
        """Remove the logging handler even when startup fails before spider_closed."""

        self._remove_error_handler()

    def _build_summary(self, spider, reason: str) -> SpiderRunSummary:
        stats = self.crawler.stats.get_stats()
        duration = 0.0
        if self.started_monotonic is not None:
            duration = max(0.0, time.monotonic() - self.started_monotonic)

        new_links = 0
        if spider.name == "suumo_links":
            new_links = len(getattr(spider, "seen_url_hashes", set()))

        status = "completed"
        warning_message = self._warning_message(spider.name, new_links)
        if reason not in SUCCESS_CLOSE_REASONS:
            status = "failed"
        elif warning_message or self.spider_errors or self.html_failed_count or self.invalid_record_count:
            status = "warning"

        latest_error = self.spider_errors[-1] if self.spider_errors else self.error_handler.latest
        exception_type = latest_error.get("error_type") if latest_error else None
        error_message = latest_error.get("error_message") if latest_error else None

        diagnostic_text = " ".join(
            filter(
                None,
                [
                    error_message,
                    self._stats_diagnostic_text(stats),
                    warning_message,
                ],
            )
        )
        possible_causes = infer_possible_causes(diagnostic_text)
        if warning_message and not possible_causes:
            possible_causes = self._empty_result_causes(spider.name, stats)

        return SpiderRunSummary(
            job_name=spider.name,
            status=status,
            close_reason=reason,
            started_at=self.started_at or current_timestamp(),
            finished_at=current_timestamp(),
            duration_seconds=round(duration, 2),
            request_count=int(stats.get("downloader/request_count", 0) or 0),
            response_count=int(stats.get("downloader/response_count", 0) or 0),
            new_links=new_links,
            html_success_count=self.html_success_count,
            html_failed_count=self.html_failed_count,
            parsed_record_count=self.parsed_record_count,
            valid_record_count=self.valid_record_count,
            invalid_record_count=self.invalid_record_count,
            batch_count=self.batch_count,
            spider_error_count=len(self.spider_errors),
            warning_message=warning_message,
            exception_type=exception_type,
            error_message=error_message,
            possible_causes=possible_causes,
        )

    def _warning_message(self, job_name: str, new_links: int) -> str | None:
        warnings: list[str] = []
        if job_name == "suumo_links" and new_links == 0:
            warnings.append("Không tìm thấy URL bất động sản mới.")
        if job_name == "suumo_html" and self.html_success_count + self.html_failed_count == 0:
            warnings.append("Không có URL mới cần tải HTML.")
        elif job_name == "suumo_html" and self.html_failed_count:
            warnings.append(f"Có {self.html_failed_count} HTML crawl thất bại.")
        if job_name == "suumo_page" and self.parsed_record_count == 0:
            warnings.append("Không có crawl task pending để parse.")
        elif job_name == "suumo_page" and self.invalid_record_count:
            warnings.append(f"Có {self.invalid_record_count} parser record không hợp lệ.")
        if self.spider_errors:
            warnings.append(f"Có {len(self.spider_errors)} spider exception chưa được xử lý.")
        return " ".join(warnings) or None

    def _empty_result_causes(self, job_name: str, stats: Mapping[str, object]) -> list[str]:
        status_403 = int(stats.get("downloader/response_status_count/403", 0) or 0)
        status_429 = int(stats.get("downloader/response_status_count/429", 0) or 0)
        if status_403:
            return ["SUUMO có thể đang chặn request hoặc IP VPN hiện tại."]
        if status_429:
            return ["SUUMO có thể đang giới hạn tần suất crawl."]
        if job_name == "suumo_links":
            return [
                "Không có bài mới, toàn bộ URL đã tồn tại, hoặc selector trang listing đã thay đổi."
            ]
        if job_name == "suumo_html":
            return ["Job links không tạo URL mới hoặc tất cả URL đã được xử lý trước đó."]
        return ["Không còn crawl task ở trạng thái pending để tạo batch mới."]

    @staticmethod
    def _stats_diagnostic_text(stats: Mapping[str, object]) -> str:
        parts = []
        for key, value in stats.items():
            if key.startswith("downloader/exception_type_count/") and value:
                parts.append(f"{key}={value}")
            elif key.startswith("downloader/response_status_count/") and value:
                parts.append(f"{key}={value}")
        return " ".join(parts)

    def _send_summary(self, summary: SpiderRunSummary) -> None:
        title_by_status = {
            "completed": "JOB HOÀN THÀNH",
            "warning": "JOB HOÀN THÀNH CÓ CẢNH BÁO",
            "failed": "JOB THẤT BẠI",
        }
        fields: dict[str, object] = {
            "Job": summary.job_name,
            "Trạng thái đóng": summary.close_reason,
            "Host": machine_name(),
            "Bắt đầu": summary.started_at,
            "Kết thúc": summary.finished_at,
            "Thời gian chạy": f"{summary.duration_seconds:.2f} giây",
            "Requests": summary.request_count,
            "Responses": summary.response_count,
        }
        if summary.job_name == "suumo_links":
            fields["URL mới"] = summary.new_links
        elif summary.job_name == "suumo_html":
            fields["HTML thành công"] = summary.html_success_count
            fields["HTML thất bại"] = summary.html_failed_count
        elif summary.job_name == "suumo_page":
            fields["Records đã parse"] = summary.parsed_record_count
            fields["Records valid"] = summary.valid_record_count
            fields["Records invalid"] = summary.invalid_record_count
            fields["Batches"] = summary.batch_count

        fields["Cảnh báo"] = summary.warning_message
        if summary.status == "failed":
            fields["Exception type"] = summary.exception_type or "SpiderClosed"
            fields["Error message"] = summary.error_message or summary.close_reason
        elif summary.exception_type:
            fields["Lỗi gần nhất"] = (
                f"{summary.exception_type}: {summary.error_message or 'không có nội dung'}"
            )

        self.notifier.send_message(
            build_event_message(
                title_by_status[summary.status],
                fields,
                possible_causes=summary.possible_causes,
            )
        )

    @staticmethod
    def _safe_run_id(value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", value)

    def _write_summary(self, summary: SpiderRunSummary) -> None:
        run_id = self._safe_run_id(os.getenv("TELEGRAM_PIPELINE_RUN_ID", "").strip())
        summary_root = os.getenv("TELEGRAM_SUMMARY_DIR", "").strip()
        if not run_id or not summary_root:
            return

        try:
            run_directory = Path(summary_root) / run_id
            run_directory.mkdir(parents=True, exist_ok=True)
            target = run_directory / f"{summary.job_name}.json"
            temporary = target.with_suffix(".json.tmp")
            temporary.write_text(
                json.dumps(asdict(summary), ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(target)
        except OSError as exc:
            LOGGER.warning("Could not persist Telegram job summary: %s", exc)

    def _remove_error_handler(self) -> None:
        root_logger = logging.getLogger()
        if self.error_handler in root_logger.handlers:
            root_logger.removeHandler(self.error_handler)
