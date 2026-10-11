import unittest
from unittest.mock import Mock
import tracing


class TracingTest(unittest.TestCase):
    def test_job_error_preserves_exception_without_exporting_its_message(self):
        import os
        os.environ.setdefault('IMPORT_KEY', 'test-only')
        import main
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        from opentelemetry.trace import StatusCode
        from unittest.mock import patch
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        @main.track_job
        def job_trace_failure():
            raise ValueError('secret-token')
        with patch.object(main, 'tracer', provider.get_tracer('test')):
            with self.assertRaisesRegex(ValueError, 'secret-token'):
                job_trace_failure()
        span = exporter.get_finished_spans()[0]
        self.assertEqual(span.attributes['job.name'], 'trace_failure')
        self.assertEqual(span.status.status_code, StatusCode.ERROR)
        self.assertFalse(span.events)
        self.assertFalse(span.status.description)
        provider.shutdown()

    def test_request_hook_replaces_sensitive_url_attributes(self):
        span = Mock()
        span.is_recording.return_value = True
        tracing.redact_request(span, Mock(url='https://example.test/?import_key=secret&data=private'))
        values = dict(call.args for call in span.set_attribute.call_args_list)
        self.assertEqual(values['http.url'], '[redacted]')
        self.assertEqual(values['url.full'], '[redacted]')
        self.assertNotIn('secret', str(values))

    def test_disabled_tracing_does_not_install_provider(self):
        from unittest.mock import patch
        with patch.dict('os.environ', {}, clear=True), patch.object(tracing.trace, 'set_tracer_provider') as install:
            self.assertIsNone(tracing.configure())
            install.assert_not_called()
