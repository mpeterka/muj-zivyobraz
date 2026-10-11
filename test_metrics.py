import os
import unittest
from unittest.mock import patch, Mock
from urllib.request import urlopen

os.environ.setdefault('IMPORT_KEY', 'test-only')
import main


class MetricsTest(unittest.TestCase):
    def test_metrics_endpoint_is_reachable(self):
        self.assertTrue(hasattr(main, 'start_http_server'))
        server, thread = main.start_http_server(0, addr='127.0.0.1')
        try:
            with urlopen(f'http://127.0.0.1:{server.server_port}/metrics') as response:
                body = response.read().decode()
            self.assertIn('zivyobraz_uploads_total', body)
            self.assertIn('zivyobraz_build_info{version=', body)
            self.assertIn('zivyobraz_application_start_timestamp_seconds', body)
            self.assertIn('zivyobraz_job_last_run_timestamp_seconds{task="popelnice"}', body)
            self.assertNotIn(main.IMPORT_KEY, body)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_failed_upload_is_counted_without_recording_success(self):
        self.assertTrue(hasattr(main, 'UPLOADS'))
        before = main.UPLOADS.labels(result='error')._value.get()
        last_success = main.LAST_UPLOAD_SUCCESS._value.get()
        with patch.object(main.requests, 'get', side_effect=main.requests.RequestException('timeout')):
            with self.assertLogs(level='ERROR'):
                self.assertFalse(main.call_function('popelnice', 'dot'))
        self.assertEqual(main.UPLOADS.labels(result='error')._value.get(), before + 1)
        self.assertEqual(main.LAST_UPLOAD_SUCCESS._value.get(), last_success)

    def test_successful_upload_is_counted(self):
        self.assertTrue(hasattr(main, 'UPLOADS'))
        before = main.UPLOADS.labels(result='success')._value.get()
        with patch.object(main.requests, 'get', return_value=Mock(status_code=200)):
            self.assertTrue(main.call_function_multiple({'popelnice': 'dot'}))
        self.assertEqual(main.UPLOADS.labels(result='success')._value.get(), before + 1)
        self.assertGreater(main.LAST_UPLOAD_SUCCESS._value.get(), 0)

    def test_job_exception_is_counted_and_propagated(self):
        self.assertTrue(hasattr(main, 'track_job'))
        @main.track_job
        def job_test_failure():
            raise ValueError('failed')
        with self.assertRaises(ValueError):
            job_test_failure()
        self.assertEqual(main.JOB_RUNS.labels(task='test_failure', result='error')._value.get(), 1)
        self.assertGreater(main.JOB_LAST_RUN.labels(task='test_failure')._value.get(), 0)
