import os
from opentelemetry import trace


def redact_request(span, request):
    if span and span.is_recording():
        for key in ('http.url', 'url.full', 'url.query', 'url.path'):
            span.set_attribute(key, '[redacted]')


def configure():
    if not os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'):
        return None
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.requests import RequestsInstrumentor

    provider = TracerProvider(resource=Resource({
        'service.name': 'muj-zivyobraz',
        'deployment.environment.name': 'production',
    }))
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(timeout=5), max_queue_size=256,
        max_export_batch_size=64, schedule_delay_millis=5000,
    ))
    trace.set_tracer_provider(provider)
    RequestsInstrumentor().instrument(request_hook=redact_request)
    return provider
