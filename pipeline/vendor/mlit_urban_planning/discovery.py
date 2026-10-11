"""Adapted from pinned upstream scrape.py; see NOTICE.md and LICENSE."""
import datetime as dt
import re
from typing import Optional
from bs4 import BeautifulSoup
_REIWA_KANJI = re.compile(r"令和\s*(\d+)\s*年\s*(\d+)\s*月\s*(\d+)\s*日")
_REIWA_SHORT = re.compile(r"[RＲ]\s*(\d+)\s*[.．]\s*(\d+)\s*[.．]\s*(\d+)")


def _reiwa_to_iso(y: int, m: int, d: int) -> str:
    """令和y年m月d日 -> ISO 日付文字列 (令和元年 = 2019)。"""
    return dt.date(2018 + y, m, d).isoformat()


def parse_reiwa_dates(text: str) -> list[str]:
    """テキスト中の令和表記の日付を ISO 文字列のリストで返す。"""
    out: list[str] = []
    for y, m, d in _REIWA_KANJI.findall(text):
        out.append(_reiwa_to_iso(int(y), int(m), int(d)))
    for y, m, d in _REIWA_SHORT.findall(text):
        out.append(_reiwa_to_iso(int(y), int(m), int(d)))
    return out


def _geojson_column_index(header_cells: list[str]) -> Optional[int]:
    for i, txt in enumerate(header_cells):
        if "GeoJSON形式" in txt.replace(" ", ""):
            return i
    return None


def parse_sources(html: str) -> list[dict]:
    """ダウンロードページ HTML から都道府県ごとの GeoJSON zip 情報を抽出。

    返り値: [{pref, url, content_id, note, modified}] を 47 件。
    """
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        # ヘッダ行（GeoJSON形式 を含む）を探し、列 index を確定
        col_idx = None
        header_row_i = None
        for i, tr in enumerate(rows):
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            idx = _geojson_column_index(cells)
            if idx is not None:
                col_idx, header_row_i = idx, i
                break
        if col_idx is None:
            continue

        sources: list[dict] = []
        for tr in rows[header_row_i + 1 :]:
            cells = tr.find_all(["th", "td"])
            if len(cells) <= col_idx:
                continue
            pref = cells[0].get_text(strip=True)
            if not pref or pref == "都道府県":
                continue
            cell = cells[col_idx]
            link = cell.find("a", href=re.compile(r"\.zip$"))
            if link is None:
                continue
            href = link["href"]
            url = href if href.startswith("http") else "https://www.mlit.go.jp" + href
            note = cell.get_text(" ", strip=True)
            dates = parse_reiwa_dates(note)
            sources.append(
                {
                    "pref": pref,
                    "url": url,
                    "content_id": url.rsplit("/", 1)[-1].removesuffix(".zip"),
                    "note": note,
                    "modified": max(dates) if dates else None,
                }
            )
        if sources:
            return sources
    raise RuntimeError("GeoJSON列を含むテーブルが見つかりませんでした（ページ構造変更の可能性）")
