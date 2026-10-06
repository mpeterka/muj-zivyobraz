import unittest
from datetime import datetime
from unittest.mock import patch

import requests

from functions import klementinum


class KlementinumTest(unittest.TestCase):
    def setUp(self):
        klementinum._monthly_records.cache_clear()

    def tearDown(self):
        klementinum._monthly_records.cache_clear()

    def test_daily_records_from_official_csv(self):
        header = 'STATION,ELEMENT,TIMEFUNC,DT,VALUE,FLAG,QUALITY,\n'
        data = {
            'T': '0-203-0-11514,T,AVG,1900-10-06T00:00Z,10.0,,0.0,\n'
                 '0-203-0-11514,T,AVG,2000-10-06T00:00Z,14.0,,0.0,\n'
                 '0-203-0-11514,T,07:00,2000-10-06T07:00Z,99.0,,0.0,\n'
                 '0-203-0-11514,T,AVG,2026-10-06T00:00Z,99.0,,0.0,\n'
                 '0-203-0-11514,T,AVG,2001-10-06T00:00Z,99.0,,1.0,\n'
                 '0-203-0-11514,T,AVG,2002-10-06T00:00Z,nan,,0.0,\n'
                 '0-203-0-11514,T,AVG,2000-09-07T00:00Z,99.0,,0.0,\n',
            'TMA': '0-203-0-11514,TMA,20:00,1900-10-06T20:00Z,20.0,,0.0,\n'
                   '0-203-0-11514,TMA,20:00,2000-10-06T20:00Z,26.0,,0.0,\n',
            'TMI': '0-203-0-11514,TMI,20:00,1900-10-06T20:00Z,-2.0,,0.0,\n'
                   '0-203-0-11514,TMI,20:00,2000-10-06T20:00Z,1.0,,0.0,\n',
        }

        def get(url, **kwargs):
            element = url.rsplit('-', 1)[-1].removesuffix('.csv')
            response = requests.Response()
            response.status_code = 200
            response._content = (header + data.get(element, '')).encode('utf-8')
            response._content_consumed = True
            return response

        with patch.object(klementinum.requests, 'get', side_effect=get), \
                patch.object(klementinum, 'datetime') as clock:
            clock.now.return_value = datetime(2026, 10, 6, 10)
            clock.fromisoformat.side_effect = datetime.fromisoformat
            self.assertEqual(klementinum.get_klementinum_values(), {
                'klementinum_avg': '12,0°C',
                'klementinum_max': '26,0°C 2000',
                'klementinum_min': '-2,0°C 1900',
            })

    def test_missing_source_does_not_erase_display(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'<html>No historical temperature data</html>'
        response._content_consumed = True
        with patch.object(klementinum.requests, 'get', return_value=response), \
                self.assertLogs(klementinum.logger, level='ERROR'):
            self.assertEqual(klementinum.get_klementinum_values(), {})


if __name__ == '__main__':
    unittest.main()
