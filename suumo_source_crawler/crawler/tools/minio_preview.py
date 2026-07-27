from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.object_storage import create_minio_client, split_storage_path


# Paste a MinIO storage_path here, then run:
# make -C suumo_source_crawler python3-container workdir=/app/crawler args="tools/minio_preview.py"
STORAGE_PATH = ""
OUTPUT_DIR = Path("tmp/minio_preview")
HTML_BASE_URL = "https://suumo.jp/"


def parse_args() -> argparse.Namespace:
    """Parse optional CLI overrides while keeping the edit-one-variable workflow."""

    parser = argparse.ArgumentParser(
        description="Download a MinIO object, decompress .gz payloads, and preview it.",
    )
    parser.add_argument(
        "storage_path",
        nargs="?",
        default=STORAGE_PATH,
        help="Logical MinIO path such as suumo/page_source/...html.gz or suumo/data/...json.gz.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(OUTPUT_DIR),
        help="Directory used when writing decoded HTML or --write-json output.",
    )
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write JSON to disk instead of printing the pretty JSON to stdout.",
    )
    parser.add_argument(
        "--base-url",
        default=HTML_BASE_URL,
        help="Base URL injected into HTML previews so relative CSS/image paths resolve.",
    )
    parser.add_argument(
        "--raw-html",
        action="store_true",
        help="Write HTML exactly as stored, without injecting a base URL for preview.",
    )
    return parser.parse_args()


def download_payload(storage_path: str) -> tuple[str, str, bytes]:
    """Download bytes from MinIO for a logical bucket/object path."""

    bucket_name, object_name = split_storage_path(storage_path)
    minio_client = create_minio_client()
    stored_response = minio_client.get_object(bucket_name, object_name)
    try:
        payload = stored_response.read()
    finally:
        stored_response.close()
        stored_response.release_conn()

    if object_name.endswith(".gz"):
        payload = gzip.decompress(payload)

    return bucket_name, object_name, payload


def preview_payload(
    storage_path: str,
    object_name: str,
    payload: bytes,
    output_dir: Path,
    write_json: bool,
    base_url: str,
    raw_html: bool,
) -> None:
    """Print JSON or write decoded payload to a local preview file."""

    text = payload.decode("utf-8")
    if is_json_object(object_name, text):
        preview_json(
            storage_path=storage_path,
            object_name=object_name,
            text=text,
            output_dir=output_dir,
            write_json=write_json,
        )
        return

    if is_html_object(object_name=object_name, text=text) and not raw_html:
        text = inject_html_base(text=text, base_url=base_url)

    output_path = write_preview_file(
        object_name=object_name,
        payload=text,
        output_dir=output_dir,
        suffix=".html" if object_name.endswith(".html.gz") else ".txt",
    )
    print(f"Wrote decoded payload to {output_path}")


def preview_json(
    storage_path: str,
    object_name: str,
    text: str,
    output_dir: Path,
    write_json: bool,
) -> None:
    """Pretty print JSON payloads or write them to disk."""

    parsed_json = json.loads(text)
    pretty_json = json.dumps(parsed_json, ensure_ascii=False, indent=2, sort_keys=True)
    if write_json:
        output_path = write_preview_file(
            object_name=object_name,
            payload=pretty_json,
            output_dir=output_dir,
            suffix=".json",
        )
        print(f"Wrote decoded JSON to {output_path}")
        return

    print(f"Storage path: {storage_path}")
    print(pretty_json)


def is_json_object(object_name: str, text: str) -> bool:
    """Return true when object name or decoded text indicates JSON."""

    if object_name.endswith(".json.gz") or object_name.endswith(".json"):
        return True

    stripped_text = text.lstrip()
    return stripped_text.startswith("{") or stripped_text.startswith("[")


def is_html_object(object_name: str, text: str) -> bool:
    """Return true when object name or decoded text indicates HTML."""

    if object_name.endswith(".html.gz") or object_name.endswith(".html"):
        return True

    return text.lstrip().lower().startswith(("<!doctype html", "<html"))


def inject_html_base(text: str, base_url: str) -> str:
    """Inject a base tag so root-relative SUUMO assets load in local previews."""

    normalized_base_url = base_url.strip()
    if not normalized_base_url or re.search(r"<base\s", text, flags=re.IGNORECASE):
        return text

    base_tag = f'<base href="{normalized_base_url}" />'
    if re.search(r"<head[^>]*>", text, flags=re.IGNORECASE):
        return re.sub(
            r"(<head[^>]*>)",
            rf"\1\n{base_tag}",
            text,
            count=1,
            flags=re.IGNORECASE,
        )

    return f"{base_tag}\n{text}"


def write_preview_file(
    object_name: str,
    payload: str,
    output_dir: Path,
    suffix: str,
) -> Path:
    """Write decoded text to a deterministic preview path."""

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / preview_file_name(object_name=object_name, suffix=suffix)
    output_path.write_text(payload, encoding="utf-8")
    return output_path


def preview_file_name(object_name: str, suffix: str) -> str:
    """Return a filesystem-safe preview filename derived from the MinIO object key."""

    file_name = object_name.replace("/", "__")
    if file_name.endswith(".gz"):
        file_name = file_name.removesuffix(".gz")
    current_suffix = Path(file_name).suffix
    if current_suffix:
        file_name = file_name[: -len(current_suffix)]

    return f"{file_name}{suffix}"


def main() -> None:
    """Download, decode, and preview the configured MinIO object."""

    args = parse_args()
    storage_path = args.storage_path.strip()
    if not storage_path:
        raise ValueError("storage_path is required")

    bucket_name, object_name, payload = download_payload(storage_path)
    print(
        f"Downloaded {len(payload)} decoded bytes from "
        f"bucket={bucket_name} object={object_name}",
    )
    preview_payload(
        storage_path=storage_path,
        object_name=object_name,
        payload=payload,
        output_dir=Path(args.output_dir),
        write_json=args.write_json,
        base_url=args.base_url,
        raw_html=args.raw_html,
    )


if __name__ == "__main__":
    main()
