#!/usr/bin/env python3
import os
import socket
import sys
from urllib.request import urlopen


def check_tcp(host: str, port: int, timeout: float = 3.0) -> None:
    with socket.create_connection((host, port), timeout=timeout):
        return


def check_http(url: str, timeout: float = 3.0) -> None:
    with urlopen(url, timeout=timeout) as response:
        if response.status >= 400:
            raise RuntimeError(f"{url} returned HTTP {response.status}")


def main() -> int:
    try:
        check_tcp(os.getenv("POSTGRES_HOST", "postgres"), int(os.getenv("POSTGRES_PORT", "5432")))
        check_http(os.getenv("MINIO_ENDPOINT_URL", "http://minio:9000") + "/minio/health/live")
    except Exception as exc:
        print(f"python service dependency check failed: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

