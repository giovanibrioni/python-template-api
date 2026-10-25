from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings

_configured = False


def _metrics_endpoint(traces_endpoint: str) -> str:
    """Derive the OTLP metrics URL from the traces URL used by this template."""
    if traces_endpoint.endswith("/v1/traces"):
        return f"{traces_endpoint[: -len('/v1/traces')]}/v1/metrics"
    return f"{traces_endpoint.rstrip('/')}/v1/metrics"


def setup_telemetry(app: FastAPI, engine: AsyncEngine, settings: Settings) -> None:
    """Install tracer and meter providers.

    Spans and http.server metrics are exported over OTLP only when an endpoint
    is configured. FastAPIInstrumentor records http.server.request.duration
    when the MeterProvider is set.
    """
    global _configured
    if _configured:
        return

    resource = Resource.create({SERVICE_NAME: settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        metric_exporter = OTLPMetricExporter(
            endpoint=_metrics_endpoint(settings.otel_exporter_otlp_endpoint)
        )
        reader = PeriodicExportingMetricReader(metric_exporter)
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))

    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    _configured = True
