"""MLIT HTTP/archive/metadata fixtures; no network, MinIO or warehouse."""

import io
import json
import unittest
import zipfile
from urllib.error import HTTPError, URLError
from unittest.mock import patch
from loaders import mlit_zoning_loader as m


def archive(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return out.getvalue()


class LoaderTests(unittest.TestCase):
    def test_zip_scope_japanese_and_raw_preservation(self):
        f = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[135, 35], [136, 35], [136, 36], [135, 35]]],
            },
            "properties": {"Citycode": "27100", "Pref": "大阪府", "FAR": "400"},
        }
        data = archive(
            {
                "27_大阪府/27100_大阪市/27100_youto.geojson": json.dumps(
                    {"type": "FeatureCollection", "features": [f]}
                )
            }
        )
        name, features = m.read_features(data, "27", "27100")
        self.assertEqual(features, [f])
        self.assertIn("大阪市", name)
        with self.assertRaises(ValueError):
            m.read_features(data, "27", "27200")
        f["properties"]["Citycode"] = "27200"
        with self.assertRaises(ValueError):
            m.read_features(
                archive(
                    {
                        "27_大阪府/27100_大阪市/27100_youto.geojson": json.dumps(
                            {"type": "FeatureCollection", "features": [f]}
                        )
                    }
                ),
                "27",
                "27100",
            )

    def test_path_traversal_corruption_and_duplicates(self):
        for path in ("../bad", "/etc/bad", "a\\bad", "a/../../bad", "C:/bad"):
            with self.assertRaises(ValueError):
                m.checked_archive(archive({path: "x"}))
        with self.assertRaises(zipfile.BadZipFile):
            m.checked_archive(b"not zip")
        info = zipfile.ZipInfo("link")
        info.external_attr = 0o120777 << 16
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            z.writestr(info, "target")
        with self.assertRaises(ValueError):
            m.checked_archive(out.getvalue())

    def test_metadata_row_hash_changes_same_date(self):
        ns = m.NS["s"]
        sheet = f'<worksheet xmlns="{ns}"><sheetData><row><c r="B924"><v>271004</v></c><c r="AI924" t="inlineStr"><is><t>2024/8/23</t></is></c></row></sheetData></worksheet>'
        data = archive({"xl/worksheets/sheet1.xml": sheet})
        row = m.city_metadata(data, "27100")
        self.assertEqual(row["AI"], "2024/8/23")
        other = {**row, "AH": "new details"}
        self.assertNotEqual(m.digest(row), m.digest(other))
        with self.assertRaises(ValueError):
            m.city_metadata(data, "27200")

    def test_discovery_url_change_and_source_dates(self):
        def page(content):
            return (
                '<table><tr><th>都道府県</th><th>GeoJSON形式</th></tr><tr><td>大阪府</td><td><a href="/toshi/tosiko/content/'
                + content
                + '.zip">ZIP</a>令和8年7月2日</td></tr></table>'
            )

        info = (
            '<p>令和7年度</p><a href="/toshi/tosiko/content/meta.xlsx">作成状況一覧</a>'
        )
        a = m.discover(page("old"), info)
        b = m.discover(page("new"), info)
        self.assertNotEqual(a["url"], b["url"])
        self.assertEqual(b["modified"], "2026-07-02")
        self.assertEqual(b["fiscal_year"], 2025)
        with self.assertRaises(ValueError):
            m.discover(page("x"), info + '<a href="second.xlsx">一覧</a>')
        for url in (
            "http://www.mlit.go.jp/x",
            "https://evil.example/x",
            "https://www.mlit.go.jp@evil.example/x",
        ):
            with self.assertRaises(ValueError):
                m.official_url(url)

    def test_http_retries_and_redirect_validation(self):
        class Response(io.BytesIO):
            def geturl(self):
                return "https://www.mlit.go.jp/result"

        responses = [
            HTTPError("x", 429, "slow", {"Retry-After": "7"}, None),
            URLError("timeout"),
            Response(b"ok"),
        ]

        def opener(*a, **k):
            x = responses.pop(0)
            if isinstance(x, Exception):
                raise x
            return x

        waits = []
        self.assertEqual(
            m.fetch_bytes(
                "https://www.mlit.go.jp/x", opener=opener, sleep=waits.append
            ),
            b"ok",
        )
        self.assertEqual(waits, [7, 4])
        with self.assertRaises(HTTPError):
            m.fetch_bytes(
                "https://www.mlit.go.jp/x",
                opener=lambda *a, **k: (_ for _ in ()).throw(
                    HTTPError("x", 403, "no", {}, None)
                ),
                sleep=waits.append,
            )

    def test_minio_and_database_failures_propagate(self):
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[135, 35], [136, 35], [136, 36], [135, 35]]],
            },
            "properties": {"Citycode": "27100", "Pref": "大阪府"},
        }
        geo = archive(
            {
                "27_大阪府/27100_大阪市/27100_youto.geojson": json.dumps(
                    {"type": "FeatureCollection", "features": [feature]}
                )
            }
        )
        ns = m.NS["s"]
        meta = archive(
            {
                "xl/worksheets/sheet1.xml": f'<worksheet xmlns="{ns}"><sheetData><row><c r="B1"><v>271004</v></c></row></sheetData></worksheet>'
            }
        )
        selection = "<table><tr><th>GeoJSON形式</th></tr></table>".encode()
        source = {
            "url": "https://www.mlit.go.jp/a.zip",
            "metadata_url": "https://www.mlit.go.jp/a.xlsx",
            "fiscal_year": 2025,
            "modified": None,
        }
        from minio.error import S3Error

        for fail_storage in (True, False):
            with (
                patch.object(
                    m, "fetch_bytes", side_effect=[selection, b"info", geo, meta]
                ),
                patch.object(m, "discover", return_value=source),
                patch.object(m, "Minio") as client,
                patch.object(
                    m,
                    "postgres_connection",
                    side_effect=RuntimeError("warehouse unavailable"),
                ) as db,
            ):
                client.return_value.bucket_exists.return_value = True
                client.return_value.get_object.side_effect = S3Error(
                    "NoSuchKey", "missing", "bucket", "id", "id", None
                )
                if fail_storage:
                    client.return_value.put_object.side_effect = RuntimeError(
                        "MinIO unavailable"
                    )
                with self.assertRaisesRegex(
                    RuntimeError, "MinIO" if fail_storage else "warehouse"
                ):
                    m.refresh_source()
                if fail_storage:
                    db.assert_not_called()
                else:
                    self.assertEqual(client.return_value.put_object.call_count, 3)

    def test_dry_run_does_nothing_and_content_identity(self):
        with (
            patch.object(m, "fetch_bytes", side_effect=AssertionError("HTTP")),
            patch.object(m, "postgres_connection", side_effect=AssertionError("DDL")),
            patch.object(m, "Minio", side_effect=AssertionError("storage")),
        ):
            self.assertEqual(m.refresh_source(dry_run=True)["writes"], 0)
        same_day_a = m.digest(
            ["27", "27100", m.digest(b"zip a"), m.digest({"AI": "2024/8/23"})]
        )
        same_day_b = m.digest(
            ["27", "27100", m.digest(b"zip b"), m.digest({"AI": "2024/8/23"})]
        )
        self.assertNotEqual(same_day_a, same_day_b)


if __name__ == "__main__":
    unittest.main()
