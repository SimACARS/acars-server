"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Any, Dict, Literal
from datetime import datetime as dt, timezone as tz
from unittest.mock import AsyncMock, patch

# Third Party Libraries
from fastapi.testclient import TestClient
from httpx2 import Response

# Local Libraries
from acars_server import databases
from tests.factories.atsu import ATSUAuthorisedCallsignFactory
from tests.factories.user import CallsignFactory
from tests.fixtures.airline_authorisation import create_airline_api_key
from tests.fixtures.user_authorisation import create_api_key


class Authentication:
    """Authentication Helpers"""
    def __init__(self, client:TestClient|None, build_type:Literal[
        "airline", "aircraft", "atsu"]) -> None:
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
        elif build_type == "atsu":
            self.atsu_data: databases.ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()

            self.info:Dict[str,Any] = {
                "type": build_type,
                "api_key": "NoOp",
                "logon_to": "_SYSTEM_DLIC",
                "callsign": self.atsu_data.callsign,
                "headers": {
                    "scheme": "Bearer",
                    "credentials": "unset"
                }
            }

    def logon(self) -> Response:
        """
        Logs on as a test airline to _SYSTEM_DLIC
        """
        if self.client is not None:
            response, _ = self.dlic_logon_request(
                logon_from=self.info["callsign"],
                logon_to=self.info["logon_to"],
                api_key=self.info["api_key"],
                endpoint=f"/dlic/{self.info['type']}/logon",
                client=self.client
            )
            if self.info["type"] == "aircraft":
                self.info["headers"] = {
                    "Authorization": f"Bearer {response.json()['access_token']}"}
            return response
        raise ValueError("Expected client to be TestClient")

    def dlic_logon_request(
        self,
        logon_from:str,
        logon_to:str,
        api_key:str,
        endpoint:str,
        client: TestClient):
        """Generate a DLIC logon request"""
        logon_data: dict = {
                "logon_from": logon_from,
                "logon_to": logon_to,
                "network": "vatsim",
                "created": dt.now(tz.utc).timestamp(),
                "logoff_code": "",
                "fans_1_a_atn_b1": False,
                "atn_b1": False,
                "fans_1_a": False
            }
        if client.headers.get("x-key"):
            client.headers.pop("x-key")
        client.headers.update({"x-key": api_key})
        with patch(
            "acars_server.api.routes.dlic.callsign_verification",
            new=AsyncMock(return_value=logon_from)
        ):
            response = client.post(endpoint, json=logon_data)
        client.headers.pop("x-key")

        return response, logon_data
