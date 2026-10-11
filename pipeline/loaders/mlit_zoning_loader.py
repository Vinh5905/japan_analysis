"""Immutable MLIT GeoJSON import. HTTP/MinIO/DB failures fail the task."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import time
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from minio import Minio
from psycopg.types.json import Jsonb

from loaders.suumo_batch_loader import (
    load_minio_config,
    load_warehouse_postgres_config,
    postgres_connection,
)
from vendor.mlit_urban_planning.discovery import parse_sources

SELECTION_URL = "https://www.mlit.go.jp/toshi/tosiko/toshi_tosiko_tk_000182.html"
INFO_URL = "https://www.mlit.go.jp/toshi/tosiko/toshi_tosiko_tk_000087.html"
MAX_DOWNLOAD = 512 * 1024 * 1024
MAX_EXPANDED = 1024 * 1024 * 1024
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value):
    return hashlib.sha256(
        value if isinstance(value, bytes) else canonical(value).encode()
    ).hexdigest()


def official_url(url):
    p = urlparse(url)
    if (
        p.scheme != "https"
        or p.hostname != "www.mlit.go.jp"
        or p.username
        or p.password
    ):
        raise ValueError("Only official HTTPS MLIT sources are accepted")
    return url


def fetch_bytes(url, *, opener=urlopen, sleep=time.sleep):
    official_url(url)
    for attempt in range(3):
        try:
            with opener(
                Request(url, headers={"User-Agent": "japan-analysis-MLIT/1.0"}),
                timeout=60,
            ) as response:
                official_url(response.geturl())
                data = response.read(MAX_DOWNLOAD + 1)
                if len(data) > MAX_DOWNLOAD:
                    raise ValueError("Download exceeds configured limit")
                return data
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            delay = exc.headers.get("Retry-After", "")
            sleep(max(2 ** (attempt + 1), int(delay) if delay.isdigit() else 0))
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            sleep(2 ** (attempt + 1))


def discover(selection_html, info_html, prefecture_code="27"):
    if prefecture_code != "27":
        raise ValueError("Initial supported prefecture is Osaka-fu (27)")
    sources = [s for s in parse_sources(selection_html) if s["pref"] == "大阪府"]
    if len(sources) != 1:
        raise ValueError("Expected one Osaka GeoJSON source")
    soup = BeautifulSoup(info_html, "html.parser")
    links = [
        a
        for a in soup.find_all("a", href=True)
        if re.search(r"\.xlsx(?:\?|$)", a["href"])
    ]
    # Select the metadata workbook by its link label/context.
    # Never silently select an unrelated workbook.
    labelled = [
        a
        for a in links
        if any(w in a.get_text() for w in ("作成", "一覧", "状況", "データ"))
    ]
    chosen = labelled or links
    urls = sorted(set(urljoin(INFO_URL, a["href"]) for a in chosen))
    if len(urls) != 1:
        raise ValueError(f"Ambiguous MLIT metadata workbook: {urls}")
    src = sources[0]
    src["url"] = official_url(src["url"])
    src["metadata_url"] = official_url(urls[0])
    text = unicodedata.normalize("NFKC", soup.get_text(" ", strip=True))
    years = re.findall(r"令和\s*(\d+)\s*年度", text)
    src["fiscal_year"] = 2018 + max(map(int, years)) if years else None
    return src


def checked_archive(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    total = 0
    names = set()
    for member in z.infolist():
        name = member.filename
        if not member.flag_bits & 0x800:
            try:
                name = name.encode("cp437").decode("cp932")
            except (UnicodeError, LookupError):
                pass
        if (
            "\\" in name
            or "\x00" in name
            or ":" in name
            or name.startswith("/")
            or ".." in PurePosixPath(name).parts
        ):
            raise ValueError(f"Unsafe ZIP path: {name!r}")
        if name in names:
            raise ValueError("Duplicate ZIP path")
        names.add(name)
        total += member.file_size
        if (
            total > MAX_EXPANDED
            or member.file_size > MAX_DOWNLOAD
            or member.flag_bits & 1
        ):
            raise ValueError("Unsafe archive size/encryption")
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise ValueError("ZIP symlinks are forbidden")
    return z


def city_metadata(data, city_code):
    with checked_archive(data) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(n.itertext()) for n in root.findall("s:si", NS)]
        matches = []
        for name in z.namelist():
            if not re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name):
                continue
            root = ET.fromstring(z.read(name))
            for row in root.findall(".//s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    col = re.sub(r"\d", "", cell.attrib["r"])
                    v = cell.find("s:v", NS)
                    text = (
                        v.text or ""
                        if v is not None
                        else "".join(cell.find("s:is", NS).itertext())
                        if cell.find("s:is", NS) is not None
                        else ""
                    )
                    if cell.attrib.get("t") == "s":
                        text = shared[int(text)]
                    cells[col] = text
                # Government metadata code includes a check digit.
                # GeoJSON uses five digits.
                if cells.get("B", "")[:5] == city_code:
                    matches.append(cells)
        if len(matches) != 1:
            raise ValueError(
                f"Expected one metadata row for city {city_code}; got {len(matches)}"
            )
        return matches[0]


def read_features(data, prefecture_code, city_code):
    with checked_archive(data) as z:
        files = []
        for m in z.infolist():
            n = m.filename
            if not m.flag_bits & 0x800:
                try:
                    n = n.encode("cp437").decode("cp932")
                except UnicodeError:
                    pass
            parts = PurePosixPath(n).parts
            if (
                len(parts) == 3
                and parts[0].startswith(prefecture_code + "_")
                and parts[1].startswith(city_code + "_")
                and parts[2] == city_code + "_youto.geojson"
            ):
                files.append((m, n))
        if len(files) != 1:
            raise ValueError("Expected one city zoning GeoJSON")
        m, name = files[0]
        geo = json.loads(
            z.read(m).decode("utf-8-sig"),
            parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
        )
        if geo.get("type") != "FeatureCollection" or not geo.get("features"):
            raise ValueError("Invalid/empty FeatureCollection")
        crs = canonical(geo.get("crs", {}))
        if crs != "{}" and "6668" not in crs:
            raise ValueError("Unexpected CRS; MLIT source must be JGD2011 EPSG:6668")
        for f in geo["features"]:
            p = f.get("properties", {})
            if (
                f.get("type") != "Feature"
                or str(p.get("Citycode")) != city_code
                or p.get("Pref") != "大阪府"
            ):
                raise ValueError("Feature scope/type mismatch")
            if (f.get("geometry") or {}).get("type") not in ("Polygon", "MultiPolygon"):
                raise ValueError("Expected polygon geometry")
        return name, geo["features"]


def init_tables(conn):
    conn.execute((Path(__file__).parents[1] / "warehouse/mlit_zoning.sql").read_text())


def refresh_source(
    prefecture_code="27", city_code="27100", *, dry_run=False, force_download=False
):
    if (prefecture_code, city_code) != ("27", "27100"):
        raise ValueError("Initial supported scope: Osaka-fu 27 / Osaka-shi 27100")
    if dry_run:
        return {
            "dry_run": True,
            "prefecture_code": prefecture_code,
            "city_code": city_code,
            "http_requests": 0,
            "writes": 0,
        }
    src = discover(
        fetch_bytes(SELECTION_URL).decode("utf-8"),
        fetch_bytes(INFO_URL).decode("utf-8"),
        prefecture_code,
    )
    # Intentionally download on every source check, including an unchanged content ID.
    zip_data = fetch_bytes(src["url"])
    meta_data = fetch_bytes(src["metadata_url"])
    meta = city_metadata(meta_data, city_code)
    name, features = read_features(zip_data, prefecture_code, city_code)
    zip_hash, meta_hash, city_hash = digest(zip_data), digest(meta_data), digest(meta)
    key = digest([prefecture_code, city_code, zip_hash, city_hash])
    zip_path = f"zip/{zip_hash}/source.zip"
    meta_path = f"metadata/{meta_hash}/source.xlsx"
    manifest_path = None
    manifest = {
        "dataset_key": key,
        "scope": [prefecture_code, city_code],
        "source": src,
        "zip_sha256": zip_hash,
        "metadata_sha256": meta_hash,
        "city_metadata_sha256": city_hash,
        "city_metadata": meta,
        "source_file": name,
        "feature_count": len(features),
    }
    manifest_path = f"datasets/{key}/{digest(manifest)}.json"
    cfg = load_minio_config()
    client = Minio(
        cfg.endpoint,
        access_key=cfg.access_key,
        secret_key=cfg.secret_key,
        secure=cfg.secure,
    )
    if not client.bucket_exists("mlit"):
        client.make_bucket("mlit")
    for path, data, kind in [
        (zip_path, zip_data, "application/zip"),
        (
            meta_path,
            meta_data,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (manifest_path, canonical(manifest).encode(), "application/json"),
    ]:
        # Content-addressed objects are write-once, with collision checks on retries.
        from minio.error import S3Error

        try:
            old = client.get_object("mlit", path)
        except S3Error as exc:
            if exc.code != "NoSuchKey":
                raise
            client.put_object(
                "mlit", path, io.BytesIO(data), len(data), content_type=kind
            )
        else:
            try:
                if digest(old.read()) != digest(data):
                    raise ValueError("Immutable object collision")
            finally:
                old.close()
                old.release_conn()
    as_of = re.search(r"\d{4}/\d{1,2}/\d{1,2}", meta.get("AI", ""))
    as_of_date = "/".join(as_of.group().split("/")) if as_of else None
    if as_of_date:
        from datetime import datetime

        as_of_date = datetime.strptime(as_of_date, "%Y/%m/%d").date()
    with postgres_connection(load_warehouse_postgres_config()) as conn:
        init_tables(conn)
        exists = conn.execute(
            "select 1 from raw.mlit_datasets where dataset_key=%s", (key,)
        ).fetchone()
        if exists:
            conn.execute(
                """
                UPDATE raw.mlit_datasets SET last_checked_at = now()
                WHERE dataset_key = %s
                """,
                (key,),
            )
        else:
            conn.execute(
                """
                INSERT INTO raw.mlit_datasets
                (
                    dataset_key,
                    prefecture_code,
                    city_code,
                    source_url,
                    metadata_url,
                    zip_sha256,
                    metadata_sha256,
                    city_metadata_sha256,
                    zip_object_path,
                    metadata_object_path,
                    manifest_object_path,
                    fiscal_year,
                    source_modified_date,
                    source_as_of_date,
                    city_metadata,
                    validation_status,
                    feature_count
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    'candidate',
                    %s
                )
                """,
                (
                    key,
                    prefecture_code,
                    city_code,
                    src["url"],
                    src["metadata_url"],
                    zip_hash,
                    meta_hash,
                    city_hash,
                    zip_path,
                    meta_path,
                    manifest_path,
                    src["fiscal_year"],
                    src["modified"],
                    as_of_date,
                    Jsonb(meta),
                    len(features),
                ),
            )
            with conn.cursor() as cur:
                cur.executemany(
                    "insert into raw.mlit_zoning_polygons values (%s,%s,%s,%s,%s)",
                    [
                        (key, name, i, Jsonb(f["geometry"]), Jsonb(f["properties"]))
                        for i, f in enumerate(features)
                    ],
                )
        conn.execute(
            """
            INSERT INTO raw.mlit_source_checks (
                dataset_key,
                source_url,
                metadata_url,
                manifest_object_path,
                source_modified_date,
                reused
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                key,
                src["url"],
                src["metadata_url"],
                manifest_path,
                src["modified"],
                bool(exists),
            ),
        )
    return {
        "dataset_key": key,
        "features": len(features),
        "reused": bool(exists),
        "zip_sha256": zip_hash,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--init-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force-download", action="store_true")
    p.add_argument("--prefecture-code", default="27")
    p.add_argument("--city-code", default="27100")
    args = p.parse_args()
    if args.dry_run:
        result = refresh_source(args.prefecture_code, args.city_code, dry_run=True)
    elif args.init_only:
        with postgres_connection(load_warehouse_postgres_config()) as conn:
            init_tables(conn)
        result = {"initialized": True}
    else:
        result = refresh_source(
            args.prefecture_code, args.city_code, force_download=args.force_download
        )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
