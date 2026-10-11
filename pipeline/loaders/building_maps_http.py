"""Project-owned HTTP worker, runnable in an isolated curl_cffi environment."""

import json
import math
import sys
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from vendor.google_maps import build_search_url, parse_search_response


def utcnow():
    return datetime.now(timezone.utc)


def retry_after_seconds(value, now=None):
    if not value:
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return max(0, math.ceil((parsed - (now or utcnow())).total_seconds()))
        except (TypeError, ValueError, OverflowError):
            return 0


class MapsSearchClient:
    def __init__(
        self,
        session=None,
        *,
        sleep=time.sleep,
        monotonic=time.monotonic,
        interval=3.0,
        timeout=15.0,
    ):
        if session is None:
            from curl_cffi.requests import Session
            from curl_cffi.requests.exceptions import RequestException

            self.session = Session(impersonate="chrome")
            self.transport_errors = (RequestException, TimeoutError, OSError)
        else:
            self.session = session
            self.transport_errors = (TimeoutError, OSError)
        self.sleep, self.monotonic = sleep, monotonic
        self.interval, self.timeout, self.last_started = (
            max(3.0, interval),
            timeout,
            None,
        )

    def search(self, query):
        url = build_search_url(query)
        last_error, audit = None, None
        for attempt in range(3):
            if self.last_started is not None:
                self.sleep(
                    max(0, self.interval - (self.monotonic() - self.last_started))
                )
            self.last_started = self.monotonic()
            try:
                response = self.session.get(
                    url,
                    impersonate="chrome",
                    verify=True,
                    headers={"Accept-Language": "ja-JP,ja;q=0.9"},
                    timeout=self.timeout,
                )
            except self.transport_errors as error:
                last_error = f"{type(error).__name__}: {error}"
                audit = {"url": url, "error": last_error}
            else:
                code, body, final_url = (
                    response.status_code,
                    response.text,
                    str(response.url),
                )
                audit = {"http_status": code, "url": final_url, "body": body}
                head = body[:3000].lower()
                common = {"raw_response": audit, "request_count": attempt + 1}
                if code == 429:
                    return {
                        "status": "rate_limited",
                        "retry_after_seconds": retry_after_seconds(
                            response.headers.get("Retry-After")
                        ),
                        "error_message": "HTTP 429; stop provider batch",
                        **common,
                    }
                if (
                    code in (401, 403)
                    or "/sorry/" in final_url
                    or "consent.google" in final_url
                    or any(
                        marker in head
                        for marker in ("unusual traffic", "captcha", "not a robot")
                    )
                ):
                    return {
                        "status": "blocked",
                        "error_message": "Provider block/consent; stop provider batch",
                        **common,
                    }
                if 500 <= code <= 599:
                    last_error = f"HTTP {code}"
                elif code != 200:
                    return {
                        "status": "request_error",
                        "error_message": f"HTTP {code}",
                        **common,
                    }
                else:
                    try:
                        parsed = parse_search_response(body)
                    except (ValueError, RecursionError) as error:
                        return {
                            "status": "invalid_response",
                            "error_message": str(error),
                            **common,
                        }
                    return {
                        "status": "ok",
                        "candidates": parsed["candidates"],
                        **common,
                    }
            if attempt < 2:
                self.sleep(2 ** (attempt + 1))
        return {
            "status": "request_error",
            "error_message": last_error,
            "raw_response": audit,
            "request_count": 3,
        }

    def close(self):
        self.session.close()


def main():
    request = json.load(sys.stdin)
    if not isinstance(request.get("query"), str) or not request["query"]:
        raise ValueError("Expected nonempty building query")
    client = MapsSearchClient()
    try:
        result = client.search(request["query"])
    finally:
        client.close()
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
