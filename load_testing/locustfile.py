"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import string
from datetime import datetime as dt, timezone as tz
from pathlib import Path
from random import choices, randint
from time import sleep

# Third Party Libraries
import pandas as pd
from locust import HttpUser, task, between
from loguru import logger


# Local Libraries
from dotenv import load_dotenv

PWD = Path(os.path.dirname(__file__))
CSV_FILE = os.path.join(PWD.parent, ".secret", "messages.csv")

load_dotenv(os.path.join(PWD.parent, "acars_server", ".env"))

for name in [
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
    "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT",
    "OTEL_METRICS_EXPORTER",
    "REDIS_HOST",
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
    wait_time = between(20, 50)
    callsigns = list(CALLSIGNS)

    def on_start(self):
        # Register a new user
        random_str = ''.join(choices(string.ascii_uppercase, k=3))
        self.callsign = f"{random_str}{randint(10,1000)}"
        user_cid = randint(10000, 99999999)
        user_registration = self.client.get(
            f"/test/auth/new_user/{user_cid}",
            name="/test/auth/new_user")
        if user_registration.status_code != 200:
            raise PermissionError(user_registration.text)

        user_api_key = user_registration.json()["api_key"]
        headers = {
                "x-key": user_api_key,
                "accept": "application/json"
            }

        # Log the user on
        logon_data = {
            "logon_from": self.callsign,
            "logon_to": "_ATC_EFGF",
            "created": 0,
            "network": "testing",
            "logoff_code": "",
            }
        jwt = self.client.post(
            "/dlic/aircraft/logon",
            name="/dlic/aircraft/logon",
            headers=headers,
            json=logon_data)
        if jwt.status_code != 200:
            raise PermissionError(jwt.text)
        payload = jwt.json()
        if "access_token" not in payload:
            raise KeyError(f"Unexpected response: {payload}")
        self.jwt_headers = {
            "Authorization": f"Bearer {jwt.json()['access_token']}"
        }

    @task(3)
    def poll(self):
        """Poll"""
        rsp = self.client.post("/acars/poll", name="/acars/poll", headers=self.jwt_headers)
        if rsp.status_code != 200:
            logger.error(rsp.headers)
            logger.error(rsp.text)
            logger.error(rsp.request.method)
            logger.error(rsp.request.url)
            logger.error(rsp.request.headers)
            logger.error(rsp.request.body)

    @task
    def tx_data(self):
        """Transmit Data"""
        row = df.iloc[randint(0, len(df) - 1)]
        if str(row["Type"]) == "ads":
            msg_type = "ads-c"
        else:
            msg_type = str(row["Type"])

        if len(str(row["To"])) < 4:
            msg_to = f"_COY_{row['To']}"
        else:
            msg_to = row['To']

        msg = {
            "msg_from": self.callsign,
            "msg_to": msg_to,
            "msg_type": msg_type,
            "packet": str(row["Content"]),
            "network": "testing",
            "created": dt.now(tz.utc).timestamp()
        }
        rsp = self.client.post(
            "/acars/tx/atn_vhf",
            json=msg, 
            name="/acars/tx/atn_vhf",
            headers=self.jwt_headers
            )
        if rsp.status_code != 201:
            logger.error(rsp.text)
