"""Transactional Osaka City checkbox catalogue. No host database dependency."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

CATALOG_URL = 'https://suumo.jp/chintai/osaka/city/'
# Match the spider's existing filters when the optional release setting is blank.
DEFAULT_SEARCH_URL = (
    'https://suumo.jp/jj/chintai/ichiran/FR301FC001/'
    '?ar=060&bs=040&ta=27&sc=27123&cb=0.0&ct=9999999&et=9999999'
    '&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2='
)
NAMES = json.loads(Path(__file__).with_name('area_names.json').read_text())


def literal(value):
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"


class Checkboxes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs, self.labels, self.label, self.parts = {}, [], None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('type') == 'checkbox' and attrs.get('name') == 'sc':
            key = attrs.get('id')
            if not key or key in self.inputs:
                raise ValueError('Duplicate/missing checkbox id')
            self.inputs[key] = attrs.get('value', '')
        if tag == 'label':
            self.label, self.parts = attrs.get('for'), []

    def handle_data(self, data):
        if self.label:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'label' and self.label:
            self.labels.append((self.label, ''.join(self.parts).strip()))
            self.label = None


def parse_catalog(html):
    parser = Checkboxes()
    parser.feed(html)
    rows, wards, codes = [], set(), set()
    for key, label in parser.labels:
        if not label.startswith('大阪市'):
            continue
        ward = re.sub(r'\s*\([\d,]+\)\s*$', '', label)[3:]
        sc = parser.inputs.get(key, '')
        if not ward.endswith('区') or not re.fullmatch(r'\d{5}', sc):
            raise ValueError('Invalid Osaka ward checkbox')
        if ward in wards or sc in codes:
            raise ValueError('Duplicate Osaka ward/code')
        wards.add(ward)
        codes.add(sc)
        rows.append({'ward': ward, 'sc': sc, 'display_name': NAMES.get(ward, 'Osaka ward ' + sc)})
    if not set(NAMES).issubset(wards):
        raise ValueError('Incomplete Osaka City catalogue; keep previous data')
    return rows


def ward_url(base_url, sc):
    """Preserve configured/default search filters while selecting exactly one ward."""
    parsed = urlsplit(base_url or DEFAULT_SEARCH_URL)
    if parsed.scheme != 'https' or parsed.hostname != 'suumo.jp' or not re.fullmatch(r'\d{5}', str(sc)):
        raise ValueError('Invalid SUUMO URL or ward code')
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True) if k not in {'sc', 'page'}]
    return urlunsplit(parsed._replace(query=urlencode(query + [('sc', sc)])))


def refresh(host, force=False, html=None):
    sid = host.source_id
    current = host.query(f"SELECT json_build_object('synced_at',synced_at) FROM crawl_area_catalogs WHERE source_id={sid} AND scope='osaka_city'")
    if current and current['synced_at'] and not force:
        return {'skipped': True}
    if html is None:
        with urlopen(Request(CATALOG_URL, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30) as response:
            html = response.read(2_000_001)
        if len(html) > 2_000_000:
            raise ValueError('Oversized catalogue')
        html = html.decode('utf-8')
    rows = parse_catalog(html)
    values = ','.join(f"({literal(r['ward'])},{literal(r['sc'])},{literal(r['display_name'])})" for r in rows)
    # Locked, deferred unique checks permit swapping codes. One output JSON,
    # one transaction, including timestamp; any malformed data rolls it all back.
    return host.query(f"""BEGIN;
      LOCK TABLE crawl_areas IN SHARE ROW EXCLUSIVE MODE;
      CREATE TEMP TABLE incoming_areas(ward text,sc text,name text) ON COMMIT DROP;
      INSERT INTO incoming_areas VALUES {values};
      CREATE TEMP TABLE sync_counts ON COMMIT DROP AS SELECT
       count(*) FILTER (WHERE a.area_id IS NULL) AS added,
       count(*) FILTER (WHERE a.area_id IS NOT NULL AND a.sc<>i.sc) AS updated,
       count(*) FILTER (WHERE a.sc=i.sc) AS unchanged
      FROM incoming_areas i LEFT JOIN crawl_areas a ON a.source_id={sid}
       AND a.prefecture='大阪府' AND a.municipality='大阪市' AND a.ward=i.ward;
      INSERT INTO crawl_areas(source_id,prefecture,municipality,ward,sc,display_name)
       SELECT {sid},'大阪府','大阪市',ward,sc,name FROM incoming_areas
       ON CONFLICT(source_id,prefecture,municipality,ward) DO UPDATE SET sc=excluded.sc;
      INSERT INTO crawl_area_catalogs(source_id,scope,catalog_url,synced_at)
       VALUES({sid},'osaka_city',{literal(CATALOG_URL)},now())
       ON CONFLICT(source_id,scope) DO UPDATE SET synced_at=excluded.synced_at;
      SELECT row_to_json(c) FROM sync_counts c;
      COMMIT;""")


def main():
    import argparse
    from scripts.telegram_control import Host
    from scripts.run_release_pipeline import read_env_file
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--compose-file', type=Path, required=True)
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    print(json.dumps(refresh(Host(args.env_file, args.compose_file, read_env_file(args.env_file)), args.refresh)))


if __name__ == '__main__':
    main()
