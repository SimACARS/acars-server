"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Any, Dict

# Third Party Libraries
from fastapi.testclient import TestClient
from httpx import Response

# Local Libraries
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.user import CallsignFactory
from tests.fixtures.airline_authorisation import create_airline_api_key
from tests.fixtures.user_authorisation import create_api_key


class Authentication:
    """Authentication Helpers"""
    def __init__(self, client:TestClient, build_type:str) -> None:
        self.client = client

        if build_type == "airline":
            self.airline, airline_key = create_airline_api_key()

            self.info:Dict[str,Any] = {
                "type": build_type,
                "api_key": airline_key,
                "logon_to": "_SYSTEM_DLIC",
                "callsign": self.airline.airline_callsign,
                "headers": {"x-key": airline_key}
            }
        elif build_type == "aircraft":
            callsign = CallsignFactory()
            _, aircraft_key = create_api_key()

            self.info:Dict[str,Any] = {
                "type": build_type,
                "api_key": aircraft_key,
                "logon_to": "EGKK",
                "callsign": callsign["callsign"],
                "headers": {"x-key": aircraft_key}
            }

    def logon(self) -> Response:
        """
        Logs on as a test airline to _SYSTEM_DLIC
        """
        response, _ = dlic_logon_request(
            logon_from=self.info["callsign"],
            logon_to=self.info["logon_to"],
            api_key=self.info["api_key"],
            endpoint=f"/dlic/{self.info['type']}/logon",
            client=self.client
        )
        if self.info["type"] == "aircraft":
            self.info["headers"] = {"Authorization": f"Bearer {response.json()['access_token']}"}
        return response
