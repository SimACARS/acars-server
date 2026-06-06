"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from pydantic_settings import BaseSettings

# Third Party Libraries
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from redis.observability import get_observability_instance, OTelConfig

# Local Libraries
from acars_server import __VERSION__

# Initialize OpenTelemetry
resource = Resource(attributes={
    "service.namespace": "acars",
    "service.name": "api",
    "service.version": __VERSION__
    })
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Set up OTLP exporter for traces
otlp_exporter = OTLPSpanExporter(
    endpoint=f"http://{os.getenv('OTLPS_ENDPOINT')}:{os.getenv('OTLPS_PORT')}",
    insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Create a tracer
tracer = trace.get_tracer("acars.api")

# Setup OpenTelemetry for Redis
exporter = OTLPMetricExporter(endpoint=f"http://{os.getenv('OTLPS_ENDPOINT')}:4318/v1/metrics")
reader = PeriodicExportingMetricReader(exporter=exporter, export_interval_millis=10000)
provider = MeterProvider(metric_readers=[reader])
metrics.set_meter_provider(provider)

otel = get_observability_instance()
otel.init(OTelConfig())


class Settings(BaseSettings):
    """Settings for ACARS Server"""
    testing: bool = False
