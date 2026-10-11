"""Conservative SUUMO headline extraction shared by the spider and backfill."""

import re
import unicodedata
from html.parser import HTMLParser

PARSER_VERSION = "building_name_v1"
BUILDING_RECORD_FIELDS = (
    "listing_headline_raw",
    "building_name_raw",
    "room_number_raw",
    "building_name_source",
    "building_name_parse_status",
)


class HeadlineParser(HTMLParser):
    """Collect visible H1/title text and the listing's hidden clipkey."""

    def __init__(self):
        """Initialize the small HTML collector without network dependencies."""
        super().__init__(convert_charrefs=True)
        self.headlines = []
        self.title = []
        self.capture = None
        self.buffer = []
        self.property_code = None

    def handle_starttag(self, tag, attrs):
        """Select the detail headline, title and listing identity input."""
        attrs = dict(attrs)
        if tag == "input" and (
            attrs.get("name") == "clipkey" or attrs.get("id") == "clipkey"
        ):
            self.property_code = attrs.get("value")
        if tag == "title" or (
            tag == "h1" and "section_h1-header-title" in attrs.get("class", "").split()
        ):
            self.capture = tag
            self.buffer = []

    def handle_data(self, data):
        """Keep text inside the selected heading, including nested spans."""
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        """Finish the selected heading without losing nested text."""
        if tag == self.capture:
            text = "".join(self.buffer).strip()
            if tag == "h1":
                self.headlines.append(text)
            else:
                self.title.append(text)
            self.capture = None


def normalize_building_name(value):
    """Canonicalize spacing/case; preserve numeric and wing suffixes."""
    return (
        re.sub(r"\s+", "", unicodedata.normalize("NFKC", value or "")).lower() or None
    )


def parse_headline(headline):
    """Split only an explicit terminal room suffix and reject generic headings."""
    text = unicodedata.normalize("NFKC", headline).strip()
    match = re.search(r"(?:\s+|^)([A-Za-z0-9-]+)\s*号室$", text)
    # A digit immediately before 号室 also handles headings without a space.
    if not match:
        match = re.search(r"([0-9]+)\s*号室$", text)
    room = match.group(1) if match else None
    name = text[: match.start()].strip() if match else text
    generic = (
        not name
        or name in {"賃貸マンション", "賃貸アパート", "賃貸住宅", "物件詳細", "SUUMO"}
        or re.search(r"徒歩\s*\d+\s*分", name)
        or re.search(r"(?:線|電鉄|地下鉄|JR).+駅(?:\s|[/／])", name)
        or re.search(r"駅\s+.*(?:階建|築\d)", name)
        or re.search(
            r"(エラー|アクセスできません|ページが見つかりません|募集終了)", name
        )
    )
    return (None, None, "generic_headline") if generic else (name, room, "parsed")


def extract_building_identity(html):
    """Extract nullable building metadata; never treat a generic title as a name."""
    parser = HeadlineParser()
    parser.feed(html)
    headline = next((value for value in parser.headlines if value), None)
    source = "h1" if headline else None
    if not headline:
        title = "".join(parser.title).strip()
        match = re.match(r"^【SUUMO】\s*(.+?)[/／]", title)
        if match:
            headline, source = match.group(1).strip(), "title"
    name, room, status = (
        parse_headline(headline) if headline else (None, None, "missing_headline")
    )
    return dict(zip(BUILDING_RECORD_FIELDS, (headline, name, room, source, status)))


def extract_property_code(html):
    """Read clipkey for matching a historical HTML to its warehouse listing."""
    parser = HeadlineParser()
    parser.feed(html)
    return parser.property_code
