"""Fixture-only geocoder checks; no live HTTP or warehouse writes."""
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from loaders import suumo_geocoder as geo

QUERY = '大阪府大阪市淀川区西宮原1丁目'
FIELDS = dict(prefecture='大阪府', district=None, municipality='大阪市', ward='淀川区', locality='西宮原', chome='１')


def feature(title='大阪府大阪市淀川区西宮原一丁目', point=None):
    return {'geometry': {'type': 'Point', 'coordinates': point or [135.492401, 34.732430]},
            'properties': {'title': title}, 'type': 'Feature'}


class GeocoderTests(unittest.TestCase):
    def test_query_normalization_and_missing_parts(self):
        for value in ('１', 1, 1.0, '1.0', ' 1 '):
            self.assertEqual(geo.build_address_query({**FIELDS, 'chome': value}), QUERY)
        for value in (None, float('nan'), '', '0', '1.5', '10000', '一'):
            self.assertIsNone(geo.build_address_query({**FIELDS, 'chome': value}))
        for field in ('prefecture', 'municipality', 'locality'):
            self.assertIsNone(geo.build_address_query({**FIELDS, field: None}))
        self.assertEqual(geo.canonical_address('大阪府大阪市淀川区東三国二十一丁目'),
                         '大阪府大阪市淀川区東三国21丁目')
        self.assertEqual(geo.canonical_address(' 北一条東 二丁目 '), '北一条東2丁目')

    def test_exact_matching_and_coordinate_order(self):
        good = geo.select_geocode_result(QUERY, [feature('大阪府大阪市淀川区西宮原二丁目'), feature()])
        self.assertEqual(good['status'], 'matched')
        self.assertEqual((good['latitude'], good['longitude']), (34.732430, 135.492401))
        for point in ([34.732430,135.492401], [float('nan'),34.7], [180,91], [True,34.7]):
            self.assertEqual(geo.select_geocode_result(QUERY,[feature(point=point)])['status'], 'invalid_response')
        self.assertEqual(geo.select_geocode_result(QUERY, [])['status'], 'not_found')
        self.assertEqual(geo.select_geocode_result(QUERY, [feature('大阪府大阪市淀川区')])['status'], 'not_found')
        self.assertEqual(geo.select_geocode_result(QUERY, [feature(),feature(point=[135.5,34.7])])['status'], 'ambiguous')
        self.assertEqual(geo.select_geocode_result(QUERY, [feature(),feature()])['status'], 'matched')
        for payload in ({}, None, [None], [{'properties':{},'geometry':None}]):
            self.assertEqual(geo.select_geocode_result(QUERY,payload)['status'], 'invalid_response')

    def test_retry_after_rate_limit_and_error_status(self):
        sleep = Mock()
        error=HTTPError('url',429,'too many', {'Retry-After':'3'},None)
        response=io.BytesIO(json.dumps([feature()]).encode())
        opener=Mock(side_effect=[error,response])
        client=geo.GSIClient(opener=opener,sleep=sleep,monotonic=lambda:0)
        self.assertEqual(geo.geocode_address(QUERY,client)['status'], 'matched')
        self.assertEqual(opener.call_count,2)
        self.assertIn(unittest.mock.call(3.0),sleep.call_args_list)
        self.assertIn(unittest.mock.call(1.0),sleep.call_args_list)
        for error in (URLError('offline'),TimeoutError(),HTTPError('url',503,'bad',{},None)):
            opener=Mock(side_effect=error)
            client=geo.GSIClient(opener=opener,sleep=Mock(),monotonic=lambda:0)
            self.assertEqual(geo.geocode_address(QUERY,client)['status'],'request_error')
            self.assertEqual(opener.call_count,4)
        opener=Mock(side_effect=HTTPError('url',403,'forbidden',{},None))
        self.assertEqual(geo.geocode_address(QUERY,geo.GSIClient(opener=opener,sleep=Mock()))['status'],'request_error')
        self.assertEqual(opener.call_count,1)
        for payload in (b'not JSON', b'[NaN]', b'[1e999]'):
            client=geo.GSIClient(opener=Mock(return_value=io.BytesIO(payload)),sleep=Mock())
            self.assertEqual(geo.geocode_address(QUERY,client)['status'],'invalid_response')
        with self.assertRaises(RuntimeError):
            geo.geocode_address(QUERY,Mock(request_json=Mock(side_effect=RuntimeError('programming bug'))))

    def test_retry_schedule_and_force_preserves_success(self):
        now=datetime(2026,10,8,tzinfo=timezone.utc)
        matched=geo.merge_cached_result(None,geo.select_geocode_result(QUERY,[feature()]),now)
        self.assertFalse(geo.cache_is_due(matched,now))
        self.assertTrue(geo.cache_is_due(matched,now,force=True))
        for status,delay in [('request_error',timedelta(hours=1)),('not_found',timedelta(days=7))]:
            failed=geo.merge_cached_result(None,geo.result_record(QUERY,status),now)
            self.assertFalse(geo.cache_is_due(failed,now))
            self.assertTrue(geo.cache_is_due(failed,now+delay))
        for status in ('ambiguous','invalid_input','invalid_response'):
            failed=geo.merge_cached_result(None,geo.result_record(QUERY,status),now)
            self.assertFalse(geo.cache_is_due(failed,now+timedelta(days=30)))
        refresh=geo.merge_cached_result(matched,geo.result_record(QUERY,'request_error'),now)
        self.assertEqual(refresh['status'],'matched')
        self.assertEqual(refresh['latitude'],matched['latitude'])
        self.assertEqual(refresh['raw_response'],matched['raw_response'])
        self.assertEqual(refresh['last_attempt_status'],'request_error')
        self.assertEqual(refresh['attempt_count'],2)

    def test_loader_uses_cache_and_keeps_network_errors_per_address(self):
        connection=Mock()
        connection.execute.return_value.fetchall.return_value=[(FIELDS,), ({**FIELDS,'chome':None},)]
        context=Mock()
        context.__enter__=Mock(return_value=connection)
        context.__exit__=Mock(return_value=False)
        fresh=geo.merge_cached_result(None,geo.select_geocode_result(QUERY,[feature()]))
        with patch.object(geo,'postgres_connection',return_value=context), patch.object(geo,'read_cache',return_value={QUERY:fresh}), patch.object(geo,'geocode_address') as request, patch.object(geo,'write_cache_result') as write:
            result=geo.enrich_geographies(relation=geo.sql.Identifier('qa','observations'))
            self.assertEqual(result['cache_hits'],1)
            self.assertEqual(result['invalid_input_geographies'],1)
            request.assert_not_called();write.assert_not_called()
        with patch.object(geo,'postgres_connection',return_value=context), patch.object(geo,'read_cache',return_value={}), patch.object(geo,'geocode_address',return_value=geo.result_record(QUERY,'request_error')) as request, patch.object(geo,'write_cache_result') as write:
            result=geo.enrich_geographies(relation=geo.sql.Identifier('qa','observations'))
            self.assertEqual((result['new_addresses'],result['lookups'],result['errors']),(1,1,1))
            self.assertIsNotNone(write.call_args.args[1]['next_retry_at'])
        with patch.object(geo,'postgres_connection',return_value=context), patch.object(geo,'read_cache',return_value={}), patch.object(geo,'geocode_address') as request, patch.object(geo,'write_cache_result') as write:
            result=geo.enrich_geographies(relation=geo.sql.Identifier('qa','observations'),dry_run=True)
            self.assertEqual(result['lookups'],1)
            request.assert_not_called();write.assert_not_called()
        with patch.object(geo,'postgres_connection',side_effect=RuntimeError('DB unavailable')):
            with self.assertRaises(RuntimeError):geo.enrich_geographies()

    def test_notebook_inline_logic_parity(self):
        path=Path(__file__).resolve().parents[2]/'notebook/03_geocode_addresses.ipynb'
        # Docker exposes only this notebook read-only; local uses repository file.
        notebook=json.loads(path.read_text())
        source=next(''.join(c['source']) for c in notebook['cells']
                    if c['cell_type']=='code' and 'class GSIClient:' in ''.join(c['source']))
        namespace={}
        exec(compile(source,str(path),'exec'),namespace)
        for parts in [FIELDS,{**FIELDS,'chome':None},{**FIELDS,'chome':1.0},
                      {**FIELDS,'district':'郡','ward':None,'locality':'東三国'}]:
            self.assertEqual(namespace['build_address_query'](parts),geo.build_address_query(parts))
        for payload in [[feature()],[],[feature(),feature(point=[135.5,34.7])], [feature(point=[34.7,135.5])]]:
            a=namespace['select_geocode_result'](QUERY,payload)
            b=geo.select_geocode_result(QUERY,payload)
            a.pop('geocoded_at');b.pop('geocoded_at')
            self.assertEqual(a,b)


if __name__=='__main__':
    unittest.main()
