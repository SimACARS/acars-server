"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from pydantic_settings import BaseSettings

# Third Party Libraries
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Local Libraries
from acars_server import __VERSION__

# Initialize OpenTelemetry
resource = Resource(attributes={
    "service.name": "acars.api",
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


class Settings(BaseSettings):
    """Settings for ACARS Server"""
    testing: bool = False
