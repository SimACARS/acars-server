"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from datetime import datetime as dt, timezone as tz
from pathlib import Path
from random import randint
from time import sleep

# Third Party Libraries
import pandas as pd
from locust import HttpUser, task, between


# Local Libraries
from acars_server.databases import StoreAndForward
from dotenv import load_dotenv

PWD = Path(os.path.dirname(__file__))
CSV_FILE = os.path.join(PWD.parent, ".secret", "messages.csv")

load_dotenv(os.path.join(PWD.parent, "acars_server", ".env"))

for name in [
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_METRICS_EXPORTER",
]:
    print(name, "=", os.getenv(name))



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
    wait_time = between(1, 5)
    callsigns = list(CALLSIGNS)
    headers = {}
    user_api_key = ""
    user_cid = randint(10000, 99999999)

    def on_start(self):
        # Register a new user
        user_registration = self.client.get(
            f"/test/auth/new_user/{self.user_cid}",
            name="/test/auth/new_user")
        if user_registration.status_code == 200:
            self.user_api_key = user_registration.json()["api_key"]
            self.headers = {
                    "x-key": self.user_api_key,
                    "accept": "application/json"
                }
            sleep(randint(1,20))

            # Log the user on
            self.client.post(
                "/dlic/aircraft/logon",
                name="/acars/poll",
                headers=self.headers)

    @task(3)
    def poll(self):
        """Poll"""
        self.client.post("/acars/poll", name="/acars/poll", headers=self.headers)

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
