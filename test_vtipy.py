import json
import unittest
from unittest.mock import patch

import requests

from functions import vtipy


class VtipyTest(unittest.TestCase):
    def response(self, jokes, status=200):
        response = requests.Response()
        response.status_code = status
        response._content = ('~function(s, vtipy) {}(document.currentScript, '
                             + json.dumps(jokes, ensure_ascii=False) + ');').encode('utf-8')
        response.headers['Content-Type'] = 'text/javascript; charset=UTF-8'
        return response

    def test_selects_complete_short_joke_with_czech_characters(self):
        response = self.response(['<p>' + 'x' * 301 + '</p>',
                                  '<!-- comment --><p>Řekl jsem: <b>Ahoj!</b><br> A šel dál.</p>'])
        with patch.object(vtipy.requests, 'get', return_value=response):
            self.assertEqual(vtipy.get_vtipy_values(), {'vtipy': 'Řekl jsem: Ahoj! A šel dál.'})

    def test_does_not_send_truncated_joke(self):
        with patch.object(vtipy.requests, 'get', return_value=self.response(['x' * 301])), \
                self.assertLogs(vtipy.logger, level='WARNING'):
            self.assertEqual(vtipy.get_vtipy_values(), {})

    def test_failure_keeps_previous_display(self):
        for status in (200, 503):
            response = self.response([], status)
            response._content = b'<html>Service unavailable</html>'
            with self.subTest(status=status), \
                    patch.object(vtipy.requests, 'get', return_value=response), \
                    self.assertLogs(vtipy.logger, level='WARNING'):
                self.assertEqual(vtipy.get_vtipy_values(), {})

    def test_timeout_keeps_previous_display(self):
        with patch.object(vtipy.requests, 'get', side_effect=requests.Timeout('timeout')), \
                self.assertLogs(vtipy.logger, level='WARNING'):
            self.assertEqual(vtipy.get_vtipy_values(), {})


if __name__ == '__main__':
    unittest.main()
