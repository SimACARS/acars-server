"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from locust import HttpUser, task, between

# Local Libraries

class Poller(HttpUser):
    """Poller"""
    wait_time = between(10, 40)

    @task
    def poll(self):
        """Poll"""
        self.client.get("/test/poll/TEST1")

    @task
    def info_req_metar(self):
        """InfoReq"""
        self.client.get("/test/METAR/vatsim/TEST1")
