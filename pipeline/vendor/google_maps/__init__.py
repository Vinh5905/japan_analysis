"""MIT-derived Maps search protocol, without crawler/HTTP/storage policy.

Copyright (c) 2026 Sonagara Vasram. See LICENSE and UPSTREAM.md.
Adapted from constants.py/parser.py at the pinned upstream commit.
"""
import json
import math
import re
from urllib.parse import quote, quote_plus

from .protocol import SEARCH_PB_TEMPLATE, SEARCH_URL_TEMPLATE


def build_search_url(query, offset=0, lang='ja', gl='jp'):
    pb = SEARCH_PB_TEMPLATE.replace('{query}', quote_plus(query)).replace('{offset}', str(offset))
    return SEARCH_URL_TEMPLATE.format(lang=lang, gl=gl, query=quote_plus(query), pb=quote(pb, safe=''))


def _get(node, *indices, default=None):
    for index in indices:
        if not isinstance(node, list) or index >= len(node):
            return default
        node = node[index]
    return node


def _find_records(node):
    if not isinstance(node, list):
        return
    if (len(node) > 50 and isinstance(node[10], str)
            and re.fullmatch(r'0x[0-9a-f]{12,}:0x[0-9a-f]{10,}', node[10], re.I)
            and isinstance(node[11], str) and len(node[11]) > 1):
        yield node
    for item in node:
        yield from _find_records(item)


def _reject_number(value):
    raise ValueError('Non-finite JSON number: ' + value)


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('Non-finite JSON float')
    return number


def parse_search_response(text):
    """Require structured JSON; no regex fallback fabricating empty points.

    Keeps conflicting duplicate records so the matching layer can reject them.
    The response is a Google place record, not a viewport center.
    """
    if not isinstance(text, str) or not text.startswith(")]}'"):
        raise ValueError('Missing Maps JSON prefix')
    payload = json.loads(text[4:].lstrip(), parse_constant=_reject_number, parse_float=_finite_float)
    if isinstance(payload, dict) and isinstance(payload.get('d'), str):
        payload = json.loads(payload['d'], parse_constant=_reject_number, parse_float=_finite_float)
    if not isinstance(payload, list):
        raise ValueError('Expected Maps JSON array')
    candidates = []
    for record in _find_records(payload):
        cid = str(int(record[10].split(':')[1], 16))
        if cid == '0':
            continue
        lines = _get(record, 2, default=[])
        lines = [x for x in lines if isinstance(x, str)] if isinstance(lines, list) else []
        address = ', '.join(lines) if lines else (_get(record, 39) or _get(record, 18) or '')
        candidates.append({
            'name': record[11].strip(), 'address': address,
            'latitude': _get(record, 9, 2), 'longitude': _get(record, 9, 3),
            'place_id': _get(record, 78) or _get(record, 227, 0, 4) or None,
            'cid': cid, 'maps_url': 'https://maps.google.com/?cid=' + cid,
        })
    return {'payload': payload, 'candidates': candidates}
