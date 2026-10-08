import io
import threading
import unittest
from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

from moon_server import MoonApp, RenderBudget

PRAGUE = ZoneInfo('Europe/Prague')


def call(app, query='', method='GET', path='/moon.png', **headers):
    result = {}
    def start(status, response_headers):
        result['status'] = int(status.split()[0])
        result['headers'] = dict(response_headers)
    result['body'] = b''.join(app({'REQUEST_METHOD': method, 'PATH_INFO': path,
        'QUERY_STRING': query, 'wsgi.input': io.BytesIO(), **headers}, start))
    return result


class MoonServerTests(unittest.TestCase):
    def app(self, now=None, phase=None, render=None):
        now = now or datetime(2026, 10, 8, 23, 59, 30, tzinfo=PRAGUE)
        return MoonApp(clock=lambda: now, phase_source=phase or Mock(return_value=90),
                       renderer=render or Mock(return_value=b'png'))

    def test_response_and_midnight_expiry(self):
        app = self.app()
        result = call(app, 'style=real&width=256')
        self.assertEqual(result['status'], 200)
        self.assertEqual(result['body'], b'png')
        self.assertEqual(result['headers']['Content-Type'], 'image/png')
        self.assertEqual(result['headers']['Cache-Control'], 'public, max-age=30')
        expected = int(datetime(2026, 10, 9, tzinfo=PRAGUE).timestamp())
        self.assertEqual(result['headers']['X-Accel-Expires'], f'@{expected}')
        self.assertEqual(result['headers']['Expires'], 'Thu, 08 Oct 2026 22:00:00 GMT')
        app.renderer.assert_called_once_with(256, 128, 'real', 90)

    def test_dst_day_is_25_hours(self):
        app = self.app(datetime(2026, 10, 25, tzinfo=PRAGUE))
        self.assertEqual(call(app)['headers']['Cache-Control'], 'public, max-age=90000')

    def test_errors_are_not_cached_and_do_not_render(self):
        app = self.app()
        for query, method, path, status in [('width=1025', 'GET', '/moon.png', 400),
                ('style=real&style=voyage', 'GET', '/moon.png', 400),
                ('', 'POST', '/moon.png', 405), ('', 'GET', '/private', 404)]:
            result = call(app, query, method, path)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['headers']['Cache-Control'], 'no-store')
        app.renderer.assert_not_called()

    def test_phase_cached_across_styles_and_failure_backoff(self):
        app = self.app()
        call(app)
        call(app, 'style=real')
        app.phase_source.assert_called_once()
        failed = self.app(phase=Mock(return_value=None))
        self.assertEqual(call(failed)['status'], 503)
        self.assertEqual(call(failed)['status'], 503)
        failed.phase_source.assert_called_once()

    def test_next_day_does_not_use_old_phase(self):
        app = self.app()
        call(app)
        app.clock = lambda: datetime(2026, 10, 9, tzinfo=PRAGUE)
        app.phase_source.return_value = None
        self.assertEqual(call(app)['status'], 503)
        self.assertEqual(app.phase_source.call_count, 2)

    def test_render_crossing_midnight_is_not_cached(self):
        app = self.app()
        def render(*args):
            app.clock = lambda: datetime(2026, 10, 9, tzinfo=PRAGUE)
            return b'old'
        app.renderer = render
        result = call(app)
        self.assertEqual(result['status'], 503)
        self.assertEqual(result['headers']['Cache-Control'], 'no-store')

    def test_budget_is_global_and_refills(self):
        tick = [0.0]
        budget = RenderBudget(clock=lambda: tick[0])
        self.assertTrue(budget.take())
        self.assertTrue(budget.take())
        self.assertFalse(budget.take())
        tick[0] = 10
        self.assertTrue(budget.take())
        self.assertFalse(budget.take())
        app = self.app()
        call(app)
        call(app, 'style=real')
        self.assertEqual(call(app, 'width=129')['status'], 429)

    def test_conditional_head_and_spoofed_headers(self):
        app = self.app()
        result = call(app, HTTP_HOST='attacker', HTTP_X_FORWARDED_HOST='attacker')
        conditional = call(app, HTTP_IF_NONE_MATCH=result['headers']['ETag'])
        self.assertEqual(conditional['status'], 304)
        self.assertEqual(conditional['body'], b'')
        app = self.app()
        self.assertEqual(call(app, method='HEAD')['body'], b'')

    def test_queue_admission_is_bounded(self):
        app = self.app()
        for _ in range(5):
            self.assertTrue(app.slots.acquire(blocking=False))
        self.assertEqual(call(app)['status'], 503)
        app.phase_source.assert_not_called()
        for _ in range(5):
            app.slots.release()

    def test_render_is_serial(self):
        active = [0, 0]
        entered, release = threading.Event(), threading.Event()
        def render(*args):
            active[0] += 1
            active[1] = max(active)
            entered.set()
            release.wait(2)
            active[0] -= 1
            return b'png'
        app = self.app(render=render)
        first = threading.Thread(target=call, args=(app,))
        second = threading.Thread(target=call, args=(app, 'style=real'))
        first.start()
        self.assertTrue(entered.wait(1))
        second.start()
        release.set()
        first.join(3)
        second.join(3)
        self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(active[1], 1)


if __name__ == '__main__':
    unittest.main()
