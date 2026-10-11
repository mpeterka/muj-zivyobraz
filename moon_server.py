"""Bounded WSGI image service. Run behind the supplied nginx configuration."""
from __future__ import annotations

import hashlib
import logging
import math
import threading
import time
from datetime import datetime, time as day_time, timedelta, timezone
from email.utils import format_datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo

from functions.faze_mesice import faze_mesice
from functions.moon_image import parse_options, render_moon, REAL_LICENSE, REAL_SOURCE

PRAGUE = ZoneInfo('Europe/Prague')
logger = logging.getLogger(__name__)


def phase_for_day(day):
    phase = faze_mesice(day)
    return phase['degrees'] if phase else None


class RenderBudget:
    """Global token bucket. Used only while the render lock is held."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.tokens = 2.0
        self.updated = clock()

    def take(self):
        now = self.clock()
        self.tokens = min(2.0, self.tokens + max(0, now - self.updated) / 10)
        self.updated = now
        if self.tokens < 1:
            return False
        self.tokens -= 1
        return True


class MoonApp:
    def __init__(self, clock=None, phase_source=phase_for_day, renderer=render_moon):
        self.clock = clock or (lambda: datetime.now(PRAGUE))
        self.phase_source = phase_source
        self.renderer = renderer
        self.slots = threading.BoundedSemaphore(5)
        self.render_lock = threading.Lock()
        self.budget = RenderBudget()
        self.phase_day = None
        self.phase = None
        self.retry_phase_after = 0.0

    def __call__(self, environ, start_response):
        method = environ.get('REQUEST_METHOD', 'GET')
        def response(status, body=b'', headers=()):
            response_headers = [('Content-Type', 'text/plain; charset=utf-8'),
                                ('Cache-Control', 'no-store'), *headers]
            if status in (200, 304):
                response_headers = list(headers)
            if status != 304:
                response_headers.append(('Content-Length', str(len(body))))
            response_headers.append(('X-Content-Type-Options', 'nosniff'))
            start_response(f'{status} {HTTPStatus(status).phrase}', response_headers)
            return [b'' if method == 'HEAD' else body]

        if environ.get('PATH_INFO') != '/moon.png':
            return response(404, b'Not found')
        if method not in {'GET', 'HEAD'}:
            return response(405, b'Method not allowed', [('Allow', 'GET, HEAD')])
        try:
            width, height, style, background = parse_options(environ.get('QUERY_STRING', ''))
        except ValueError:
            return response(400, b'Invalid dimensions or style')
        if not self.slots.acquire(blocking=False):
            return response(503, b'Queue full', [('Retry-After', '10')])
        locked = False
        try:
            locked = self.render_lock.acquire(timeout=12)
            if not locked:
                return response(503, b'Render busy', [('Retry-After', '10')])
            now = self.clock().astimezone(PRAGUE)
            day = now.date()
            if self.phase_day != day:
                if time.monotonic() < self.retry_phase_after:
                    return response(503, b'Phase unavailable', [('Retry-After', '20')])
            if not self.budget.take():
                return response(429, b'Render rate exceeded', [('Retry-After', '10')])
            if self.phase_day != day:
                phase = self.phase_source(day)
                if phase is None or not math.isfinite(phase):
                    self.retry_phase_after = time.monotonic() + 20
                    return response(503, b'Phase unavailable', [('Retry-After', '20')])
                self.phase_day, self.phase = day, phase
                self.retry_phase_after = 0.0
            render_started = time.monotonic()
            data = self.renderer(width, height, style, self.phase, background)
            logger.info('moon_render date=%s style=%s width=%d height=%d background=%s phase=%.2f duration_ms=%.1f bytes=%d',
                        day.isoformat(), style, width, height, background or 'transparent', self.phase,
                        (time.monotonic() - render_started) * 1000, len(data))
            finished = self.clock().astimezone(PRAGUE)
            if finished.date() != day:
                return response(503, b'Date changed; retry', [('Retry-After', '1')])
            midnight = datetime.combine(day + timedelta(days=1), day_time(), PRAGUE)
            expires = int(midnight.timestamp())
            ttl = max(0, int(expires - finished.timestamp()))
            etag = '"' + hashlib.sha256(day.isoformat().encode() + data).hexdigest() + '"'
            headers = [('Content-Type', 'image/png'),
                       ('Cache-Control', f'public, max-age={ttl}'),
                       ('Expires', format_datetime(midnight.astimezone(timezone.utc), usegmt=True)),
                       ('X-Accel-Expires', f'@{expires}'), ('ETag', etag)]
            if style == 'real':
                headers.extend([('Link', f'<{REAL_LICENSE}>; rel="license", <{REAL_SOURCE}>; rel="describedby"'),
                                ('X-Image-Credit', 'Luc Viatour / https://lucnix.be; CC BY-SA 3.0; adapted')])
            if environ.get('HTTP_IF_NONE_MATCH') == etag:
                return response(304, headers=headers)
            return response(200, data, headers)
        except Exception:
            logger.exception('Moon request failed')
            self.retry_phase_after = time.monotonic() + 20
            return response(503, b'Image unavailable', [('Retry-After', '20')])
        finally:
            if locked:
                self.render_lock.release()
            self.slots.release()


if __name__ == '__main__':
    from waitress import serve
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    serve(MoonApp(), host='0.0.0.0', port=8080, threads=5,
          connection_limit=16, backlog=8, channel_timeout=20,
          cleanup_interval=5, max_request_header_size=4096,
          max_request_body_size=0, clear_untrusted_proxy_headers=True,
          expose_tracebacks=False)
