"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from pathlib import Path
import os
import random

# Third Party Libraries
import pandas as pd
from locust import HttpUser, task, between

# Local Libraries

PWD = Path(os.path.dirname(__file__))
CSV_FILE = os.path.join(PWD.parent, ".secret", "messages.csv")

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
callsigns = df["From"].dropna().unique().tolist() + df["To"].dropna().unique().tolist()
CALLSIGNS = list(set(callsigns))
print(CALLSIGNS)

class Poller(HttpUser):
    """Poller"""
    def on_start(self):
        self.callsigns = list(CALLSIGNS)
    wait_time = between(1, 5)

    @task(3)
    def poll(self):
        """Poll"""
        callsign = random.choice(self.callsigns)
        self.client.get(f"/test/poll/{callsign}", name="/test/poll/[callsign]")

    @task
    def tx_data(self):
        """Transmit Data"""
        row = df.sample(n=1).iloc[0]
        msg = {
            "msg_from": row["From"],
            "msg_to": row["To"],
            "msg_type": row["Type"],
            "packet": row["Content"],
            "network": row["Network"],
            "created": dt.now(tz.utc).timestamp()
        }
        self.client.post("/test/tx", json=msg, name="/test/tx")
