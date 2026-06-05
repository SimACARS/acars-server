"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from pathlib import Path
import os

# Third Party Libraries
import pandas as pd
from locust import HttpUser, task, between
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


# Local Libraries
from acars_server.databases import StoreAndForward
from dotenv import load_dotenv

PWD = Path(os.path.dirname(__file__))
CSV_FILE = os.path.join(PWD.parent, ".secret", "messages.csv")

load_dotenv(os.path.join(PWD.parent, "acars_server", ".env"))

# Initialize OpenTelemetry
resource = Resource(attributes={"service.name": "locust"})
tracer_provider = TracerProvider(resource=resource)
trace.set_tracer_provider(tracer_provider)

# Set up OTLP exporter for traces
otlp_exporter = OTLPSpanExporter(
    endpoint=f"http://{os.getenv('OTLPS_ENDPOINT')}:{os.getenv('OTLPS_PORT')}"
    insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Hoppie gets around 21k messages per day, so we can set a reasonable wait
# time to simulate real-world traffic. This will allow us to test the server's
# ability to handle a steady stream of messages without overwhelming it.

# Based on the current traffic, we can expect around 14 messages every 1 minute on average.
# To simulate this, we can set the wait time to be between 1 and 5 seconds, which will allow for some
# variability while still maintaining a realistic load on the server.

# Network   	Callsigns Online
# IVAO	        83
# None	        60
# PDAsim	    1
# VATSIM	    1068
# Total	        1212

df = pd.read_csv(CSV_FILE)
df.fillna(0.0)
callsigns = df["From"].dropna().unique().tolist() + df["To"].dropna().unique().tolist()
CALLSIGNS = list(set(callsigns))

class Poller(HttpUser):
    """Poller"""
    def on_start(self):
        self.callsigns = list(CALLSIGNS)
        self.headers = {
            "x-key": os.getenv("TEST_API_KEY"),
            "accept": "application/json"
            }
    wait_time = between(1, 5)

    @task(3)
    def poll(self):
        """Poll"""
        self.client.post(f"/acars/poll", name="/acars/poll", headers=self.headers)

    @task
    def tx_data(self):
        """Transmit Data"""
        row = df.sample(n=1).iloc[0]
        if str(row["Type"]) == "ads":
            msg_type = "ads-c"
        else:
            msg_type = str(row["Type"])

        if len(str(row["From"])) < 4:
            msg_from = f"_COY_{row['From']}"
        else:
            msg_from = row['From']

        if len(str(row["To"])) < 4:
            msg_to = f"_COY_{row['To']}"
        else:
            msg_to = row['To']

        msg = {
            "msg_from": msg_from,
            "msg_to": msg_to,
            "msg_type": msg_type,
            "packet": str(row["Content"]),
            "network": "testing",
            "created": dt.now(tz.utc).timestamp()
        }
        if StoreAndForward.model_validate(msg):
            self.client.post("/acars/tx", json=msg, name="/acars/tx", headers=self.headers)
