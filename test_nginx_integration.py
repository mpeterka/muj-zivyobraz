"""Run explicitly with MOON_TEST_URL against a freshly started test compose stack."""
import io
import http.client
import os
import time
import unittest
from urllib.parse import urlsplit

import requests
from PIL import Image


@unittest.skipUnless(os.getenv('MOON_TEST_URL'), 'Set MOON_TEST_URL for a fresh nginx integration stack')
class NginxIntegrationTests(unittest.TestCase):
    def test_cache_validation_and_limits(self):
        base = os.environ['MOON_TEST_URL'].rstrip('/') + '/moon.png'
        session = requests.Session()
        def get(query='', **kwargs):
            return session.get(base + ('?' + query if query else ''), timeout=35, **kwargs)

        voyage = get()
        self.assertEqual(voyage.status_code, 200, voyage.text[:100] if voyage.status_code != 200 else '')
        self.assertEqual(voyage.headers['X-Moon-Cache'], 'MISS')
        self.assertEqual(Image.open(io.BytesIO(voyage.content)).size, (128, 128))
        real = get('style=real')
        self.assertEqual(real.status_code, 200)
        self.assertEqual(real.headers['X-Moon-Cache'], 'MISS')
        self.assertNotEqual(voyage.content, real.content)
        self.assertIn('Luc Viatour', real.headers['X-Image-Credit'])
        time.sleep(1.1)  # A cache HIT must not reset downstream freshness after midnight.
        for query in ['height=128&style=voyage&width=128', 'style=voyage']:
            cached = get(query)
            self.assertEqual(cached.headers['X-Moon-Cache'], 'HIT')
            self.assertEqual(cached.content, voyage.content)
            self.assertEqual(cached.headers['Date'], voyage.headers['Date'])
        spoofed = get(headers={'Host': 'evil.example', 'X-Forwarded-Host': 'evil.example',
                               'Cookie': 'style=real', 'Authorization': 'ignored'})
        self.assertEqual(spoofed.content, voyage.content)
        self.assertEqual(spoofed.headers['X-Moon-Cache'], 'HIT')
        conditional = get(headers={'If-None-Match': voyage.headers['ETag']})
        self.assertEqual(conditional.status_code, 304)
        self.assertEqual(conditional.content, b'')
        head = session.head(base, timeout=10)
        self.assertEqual(head.status_code, 200)
        self.assertEqual(head.content, b'')
        for query in ['style=real&style=voyage', 'width=128&width=256',
                      'height=128&height=128', 'style=Real', 'WIDTH=128',
                      'width=1025', 'width=0128',
                      'style=real&foo=bar', 'width=128&', 'width=31',
                      'background-color=%23000&background-color=%23fff',
                      'background-color=%23xyz', 'background-color=%2523000']:
            rejected = get(query)
            self.assertEqual(rejected.status_code, 400, query)
            self.assertIn('no-store', rejected.headers['Cache-Control'])
        # requests normalizes percent-encoded unreserved characters before sending.
        target = urlsplit(base)
        raw = http.client.HTTPConnection(target.hostname, target.port, timeout=10)
        raw.request('GET', '/moon.png?width=%31%32%38')
        rejected = raw.getresponse()
        self.assertEqual(rejected.status, 400)
        self.assertIn('no-store', rejected.getheader('Cache-Control'))
        rejected.read()
        raw.close()
        exhausted = get('width=129')
        self.assertEqual(exhausted.status_code, 429)
        self.assertIn('no-store', exhausted.headers['Cache-Control'])
        self.assertIn('Retry-After', exhausted.headers)
        statuses = [get().status_code for _ in range(15)]
        self.assertIn(429, statuses)


if __name__ == '__main__':
    unittest.main()
