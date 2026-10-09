"""GSI AddressSearch: chuẩn hóa chōme và chỉ nhận kết quả cùng địa chỉ."""
import json
import math
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROVIDER = 'gsi_address_search'
QUERY_VERSION = 'chome_v1'
ENDPOINT = 'https://msearch.gsi.go.jp/address-search/AddressSearch'
ADDRESS_FIELDS = ('prefecture', 'district', 'municipality', 'ward', 'locality', 'chome')


def clean_part(value):
    """NFKC rồi bỏ khoảng trắng; không sửa chữ số nằm trong tên địa danh."""
    if value is None:
        return ''
    text = unicodedata.normalize('NFKC', str(value))
    text = re.sub(r'\s+', '', text)
    return '' if text in {'', 'nan', 'NaN', '<NA>', 'None', '-', '―'} else text


def build_address_query(parts):
    """Thiếu prefecture/municipality/locality/chōme thì không suy diễn địa chỉ."""
    values = {field: clean_part(parts.get(field)) for field in ADDRESS_FIELDS}
    chome = values['chome']
    if not all(values[field] for field in ('prefecture', 'municipality', 'locality')):
        return None
    if not re.fullmatch(r'[0-9]+(?:\.0+)?', chome):
        return None
    number = int(chome.split('.')[0])
    if not 1 <= number <= 9999:
        return None
    return ''.join(values[field] for field in ADDRESS_FIELDS[:-1]) + str(number) + '丁目'


def kanji_integer(text):
    digits = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4,
              '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
    units = {'十': 10, '百': 100, '千': 1000}
    if text.isascii() and text.isdigit():
        return int(text)
    if all(char in digits for char in text):
        return int(''.join(str(digits[char]) for char in text))
    total, current = 0, 0
    for char in text:
        if char in digits:
            current = digits[char]
        elif char in units:
            total += (current or 1) * units[char]
            current = 0
        else:
            raise ValueError('Invalid chome numeral')
    return total + current


def canonical_address(text):
    """Chỉ đổi số ngay trước 丁目 ở cuối chuỗi, ví dụ giữ nguyên 東三国."""
    text = clean_part(text)
    match = re.search(r'([0-9〇零一二三四五六七八九十百千]+)丁目$', text)
    if match:
        text = text[:match.start()] + str(kanji_integer(match.group(1))) + '丁目'
    return text


def result_record(address_query, status, **extra):
    return {'provider': PROVIDER, 'query_version': QUERY_VERSION,
            'address_query': address_query, 'status': status,
            'latitude': None, 'longitude': None, 'matched_address': None,
            'coordinate_level': None, 'raw_response': None, 'error_message': None,
            'geocoded_at': None, **extra}


def select_geocode_result(address_query, payload):
    """Không lấy kết quả đầu tiên; cần địa chỉ khớp và Point hợp lệ tại Nhật."""
    if not isinstance(payload, list):
        return result_record(address_query, 'invalid_response', raw_response=payload,
                             error_message='Expected a GeoJSON feature list')
    matches, invalid = {}, False
    for feature in payload:
        if not isinstance(feature, dict):
            invalid = True
            continue
        properties = feature.get('properties')
        geometry = feature.get('geometry')
        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            invalid = True
            continue
        title = properties.get('title')
        if not isinstance(title, str) or canonical_address(title) != canonical_address(address_query):
            continue
        coordinates = geometry.get('coordinates')
        if (geometry.get('type') != 'Point' or not isinstance(coordinates, list)
                or len(coordinates) != 2 or any(isinstance(n, bool) or not isinstance(n, (int, float))
                                               or not math.isfinite(n) for n in coordinates)):
            invalid = True
            continue
        longitude, latitude = coordinates  # GeoJSON trả [kinh độ, vĩ độ].
        # Giới hạn toàn cầu + sanity check Nhật để bắt đảo thứ tự/điểm ở nước khác.
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90
                and 122 <= longitude <= 154 and 20 <= latitude <= 46):
            invalid = True
            continue
        matches[(float(longitude), float(latitude))] = title
    if invalid:
        return result_record(address_query, 'invalid_response', raw_response=payload,
                             error_message='Malformed candidate or invalid coordinates')
    if len(matches) > 1:
        return result_record(address_query, 'ambiguous', raw_response=payload,
                             error_message='Multiple matching addresses have different points')
    if not matches:
        return result_record(address_query, 'not_found', raw_response=payload,
                             error_message='No exact chome address match')
    (longitude, latitude), title = next(iter(matches.items()))
    return result_record(address_query, 'matched', raw_response=payload,
                         latitude=latitude, longitude=longitude, matched_address=title,
                         coordinate_level='chome', geocoded_at=datetime.now(timezone.utc).isoformat())


def reject_nonfinite_json(value):
    raise ValueError('Non-finite JSON number: ' + value)


def finite_json_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Non-finite JSON float: ' + value)
    return number


class GSIClient:
    """Rate limit áp dụng cho mọi request, kể cả retry."""
    def __init__(self, *, timeout=15, retries=3, min_interval=1.0,
                 opener=urlopen, sleep=time.sleep, monotonic=time.monotonic):
        if timeout <= 0 or retries < 0 or min_interval < 1:
            raise ValueError('timeout > 0, retries >= 0, min_interval >= 1 required')
        self.timeout, self.retries, self.min_interval = timeout, retries, min_interval
        self.opener, self.sleep, self.monotonic = opener, sleep, monotonic
        self.last_request = None

    def request_json(self, address_query):
        url = ENDPOINT + '?' + urlencode({'q': address_query})
        for attempt in range(self.retries + 1):
            if self.last_request is not None:
                self.sleep(max(0, self.min_interval - (self.monotonic() - self.last_request)))
            self.last_request = self.monotonic()
            try:
                request = Request(url, headers={'User-Agent': 'japan-analysis/1.0 (address enrichment)',
                                               'Accept': 'application/json'})
                with self.opener(request, timeout=self.timeout) as response:
                    return json.load(response, parse_constant=reject_nonfinite_json, parse_float=finite_json_float), attempt + 1
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.retries:
                    raise
                delay = 2 ** attempt
                retry_after = exc.headers.get('Retry-After') if exc.headers else None
                if retry_after:
                    try:
                        delay = max(delay, float(retry_after))
                    except ValueError:
                        try:
                            delay = max(delay, (parsedate_to_datetime(retry_after)
                                                - datetime.now(timezone.utc)).total_seconds())
                        except (ValueError, TypeError):
                            pass
                self.sleep(delay)
            except (URLError, TimeoutError, OSError):
                if attempt == self.retries:
                    raise
                self.sleep(2 ** attempt)


def geocode_address(address_query, client=None):
    if not address_query:
        return result_record(address_query, 'invalid_input', error_message='Missing chome address')
    client = client or GSIClient()
    try:
        payload, requests = client.request_json(address_query)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return result_record(address_query, 'request_error', error_message=str(exc)[:1000])
    except (ValueError, UnicodeError) as exc:
        return result_record(address_query, 'invalid_response', error_message=str(exc)[:1000])
    return {**select_geocode_result(address_query, payload), 'request_count': requests}


def cache_is_due(cached, now=None, force=False):
    if force or not cached:
        return True
    if cached['status'] == 'matched':
        return False
    due = cached.get('next_retry_at')
    if not due:
        return False
    if isinstance(due, str):
        due = datetime.fromisoformat(due)
    return due <= (now or datetime.now(timezone.utc))


def merge_cached_result(previous, result, now=None):
    """Force thất bại giữ nguyên điểm đã được nhận; lưu lỗi của lần thử mới."""
    now = now or datetime.now(timezone.utc)
    result = {**result, 'attempt_count': (previous or {}).get('attempt_count', 0) + 1,
              'last_attempted_at': now.isoformat(), 'next_retry_at': None}
    if previous and previous['status'] == 'matched' and result['status'] != 'matched':
        return {**previous, 'attempt_count': result['attempt_count'],
                'last_attempted_at': result['last_attempted_at'],
                'error_message': 'Refresh ' + result['status'] + ': ' + (result.get('error_message') or ''),
                'last_attempt_status': result['status'], 'last_attempt_response': result.get('raw_response')}
    result['last_attempt_status'] = result['status']
    result['last_attempt_response'] = result.get('raw_response')
    days = 7 if result['status'] == 'not_found' else None
    if days:
        result['next_retry_at'] = (now + timedelta(days=days)).isoformat()
    elif result['status'] == 'request_error':
        result['next_retry_at'] = (now + timedelta(hours=1)).isoformat()
    return result


# Notebook giữ bản code inline; test parity bảo vệ hai đường chạy.
import argparse
import os
from pathlib import Path

from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from loaders.suumo_batch_loader import load_warehouse_postgres_config, postgres_connection

CACHE_COLUMNS = ('provider', 'query_version', 'address_query', 'latitude', 'longitude',
                 'matched_address', 'coordinate_level', 'status', 'attempt_count',
                 'last_attempted_at', 'next_retry_at', 'error_message', 'raw_response',
                 'geocoded_at', 'last_attempt_status', 'last_attempt_response')


def ensure_cache_table(config=None):
    migration = Path(__file__).resolve().parents[1] / 'warehouse/suumo_address_geocodes.sql'
    with postgres_connection(config or load_warehouse_postgres_config()) as conn:
        conn.execute(migration.read_text(encoding='utf-8'))


def observation_relation():
    project = Path(os.getenv('DBT_PROJECT_DIR', str(Path(__file__).resolve().parents[2] / 'analytics/dbt')))
    manifest = json.loads((project / 'target/airflow/manifest.json').read_text())
    node = manifest['nodes']['model.japan_analysis.int_suumo__mart_observations']
    return sql.Identifier(node['schema'], node['alias'])


def read_cache(conn):
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute('select * from raw.suumo_address_geocodes where provider=%s and query_version=%s',
                       (PROVIDER, QUERY_VERSION))
        return {row['address_query']: dict(row) for row in cursor.fetchall()}


def write_cache_result(conn, result):
    values = [Jsonb(result.get(column)) if column in {'raw_response', 'last_attempt_response'}
              else result.get(column) for column in CACHE_COLUMNS]
    updates = [sql.SQL('{} = EXCLUDED.{}').format(sql.Identifier(column), sql.Identifier(column))
               for column in CACHE_COLUMNS[3:]]
    conn.execute(sql.SQL('INSERT INTO raw.suumo_address_geocodes ({}) VALUES ({}) '
                        'ON CONFLICT (provider, query_version, address_query) DO UPDATE SET {}').format(
        sql.SQL(', ').join(map(sql.Identifier, CACHE_COLUMNS)),
        sql.SQL(', ').join(sql.Placeholder() for _ in CACHE_COLUMNS), sql.SQL(', ').join(updates)), values)
    conn.commit()  # Lưu từng địa chỉ, có thể tiếp tục sau khi process bị ngắt.


def enrich_geographies(*, config=None, relation=None, limit=None, dry_run=False, force=False,
                       client=None, import_cache=None):
    if limit is not None and limit < 1:
        raise ValueError('limit must be positive')
    config = config or load_warehouse_postgres_config()
    summary = {'unique_addresses': 0, 'invalid_input_geographies': 0, 'new_addresses': 0,
               'cache_hits': 0, 'deferred': 0, 'lookups': 0, 'matched': 0, 'unmatched': 0,
               'errors': 0, 'imported': 0, 'dry_run': dry_run}
    with postgres_connection(config) as conn:
        cached = read_cache(conn)
        rows = conn.execute(sql.SQL('select distinct geography_attributes from {}').format(
            relation or observation_relation())).fetchall()
    queries = set()
    for (parts,) in rows:
        query = build_address_query(parts)
        if query:
            queries.add(query)
        else:
            summary['invalid_input_geographies'] += 1
    summary['unique_addresses'] = len(queries)
    imported = json.loads(Path(import_cache).read_text(encoding='utf-8')) if import_cache else {}
    if not isinstance(imported, dict):
        raise ValueError('Notebook cache must be a JSON object')
    client = client or GSIClient()
    with postgres_connection(config) as conn:
        for query in sorted(queries):
            previous = cached.get(query)
            # Có thể dùng kết quả notebook để tránh gọi lại toàn bộ bộ địa chỉ.
            key = json.dumps([PROVIDER, QUERY_VERSION, query], ensure_ascii=False)
            candidate = imported.get(key)
            if not dry_run and not previous and candidate and candidate.get('status') == 'matched':
                if (candidate.get('provider'), candidate.get('query_version'), candidate.get('address_query')) != (PROVIDER, QUERY_VERSION, query):
                    raise ValueError('Notebook cache identity mismatch')
                checked = select_geocode_result(query, candidate.get('raw_response'))
                if checked['status'] != 'matched' or any(checked[field] != candidate.get(field)
                                                       for field in ('latitude', 'longitude', 'matched_address', 'coordinate_level')):
                    raise ValueError('Notebook cached point does not match validated response')
                write_cache_result(conn, candidate)
                previous = cached[query] = candidate
                summary['imported'] += 1
            if previous and not cache_is_due(previous, force=force):
                summary['cache_hits'] += int(previous['status'] == 'matched')
                summary['deferred'] += int(previous['status'] != 'matched')
                continue
            summary['new_addresses'] += int(previous is None)
            if limit is not None and summary['lookups'] >= limit:
                continue
            summary['lookups'] += 1
            if dry_run:
                continue
            result = geocode_address(query, client)
            merged = merge_cached_result(previous, result)
            write_cache_result(conn, merged)
            cached[query] = merged
            summary['matched'] += int(result['status'] == 'matched')
            summary['unmatched'] += int(result['status'] in {'not_found', 'ambiguous'})
            summary['errors'] += int(result['status'] in {'invalid_input', 'invalid_response', 'request_error'})
    return summary


def main():
    parser = argparse.ArgumentParser(description='Geocode distinct dbt chome addresses into warehouse cache')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--dry-run', action='store_true', help='Read only: no DDL, cache writes or HTTP')
    parser.add_argument('--force', action='store_true', help='Refresh even matched/deferred entries')
    parser.add_argument('--init-only', action='store_true', help='Create loader-owned cache source without HTTP')
    parser.add_argument('--import-cache', help='Import validated matched entries from notebook JSON cache')
    args = parser.parse_args()
    if args.dry_run and args.init_only:
        parser.error('--dry-run cannot be combined with --init-only')
    if not args.dry_run:
        ensure_cache_table()
    if args.init_only:
        print(json.dumps({'initialized': True}))
        return
    print(json.dumps(enrich_geographies(limit=args.limit, dry_run=args.dry_run, force=args.force,
                                       import_cache=args.import_cache), ensure_ascii=False))


if __name__ == '__main__':
    main()
