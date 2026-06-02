"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from datetime import datetime as dt, timezone as tz
from unittest.mock import AsyncMock, patch

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import AirlineApiKey, ApiKey, DataLinkInitiationCapability
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import CallsignFactory, UserApiKeyFactory

class TestAirlineLogon:
    """Airline Logon"""
    def test_dlic_airline_logon(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        airline: AirlineApiKey = AirlineApiKeyFactory()
        login_data: dict = {
            "logon_from": airline.airline_callsign,
            "logon_to": "_SYSTEM_DLIC",
            "network": "vatsim",
            "created": dt.now(tz.utc).timestamp(),
            "logoff_code": "",
            "fans_1_a_atn_b1": False,
            "atn_b1": False,
            "fans_1_a": False
        }
        client.headers.update({"x-key": airline.api_key})

        response = client.post("/dlic/airline/logon", json=login_data)
        print(response.json())

        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json()["status"] == "logged on"
        obj = DataLinkInitiationCapability.model_validate(response.json()["data"])
        assert obj
        assert re.fullmatch(r"\d+\.\d+", str(obj.created))
        assert obj.logon_from == f"_COY_{airline.airline_callsign}"
        assert obj.logon_to == "_SYSTEM_DLIC"
        assert obj.network == "vatsim"
        assert obj.fans_1_a_atn_b1 is False
        assert obj.atn_b1 is False
        assert obj.fans_1_a is False
        assert re.fullmatch(r"[a-f0-9]{64}", obj.logoff_code)
        assert obj.logoff_code != login_data["logoff_code"]

class TestAircraftLogon:
    """Aircraft Logon"""
    def test_dlic_aircraft_logon(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        callsign = CallsignFactory()
        aircraft: ApiKey = UserApiKeyFactory()
        login_data: dict = {
            "logon_from": callsign["callsign"],
            "logon_to": "EGKK",
            "network": "vatsim",
            "created": dt.now(tz.utc).timestamp(),
            "logoff_code": "",
            "fans_1_a_atn_b1": False,
            "atn_b1": False,
            "fans_1_a": False
        }

        client.headers.update({"x-key": aircraft.api_key})

        with patch(
            "acars_server.api.routes.dlic.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response = client.post("/dlic/aircraft/logon", json=login_data)

        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json()["status"] == "logged on"
        obj = DataLinkInitiationCapability.model_validate(response.json()["data"])
        assert obj
        assert re.fullmatch(r"\d+\.\d+", str(obj.created))
        assert obj.logon_from == callsign["callsign"]
        assert obj.logon_to == "EGKK"
        assert obj.network == "vatsim"
        assert obj.fans_1_a_atn_b1 is False
        assert obj.atn_b1 is False
        assert obj.fans_1_a is False
        assert re.fullmatch(r"[a-f0-9]{64}", obj.logoff_code)
        assert obj.logoff_code != login_data["logoff_code"]

    def test_dlic_aircraft_logon_duplicate(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        callsign = CallsignFactory()
        aircraft: ApiKey = UserApiKeyFactory()
        login_data: dict = {
            "logon_from": callsign["callsign"],
            "logon_to": "EGKK",
            "network": "vatsim",
            "created": dt.now(tz.utc).timestamp(),
            "logoff_code": "",
            "fans_1_a_atn_b1": False,
            "atn_b1": False,
            "fans_1_a": False
        }

        client.headers.update({"x-key": aircraft.api_key})

        with patch(
            "acars_server.api.routes.dlic.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response = client.post("/dlic/aircraft/logon", json=login_data)

        assert response.status_code == 200

        with patch(
            "acars_server.api.routes.dlic.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response = client.post("/dlic/aircraft/logon", json=login_data)

        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json() == {
            "status": "already logged on",
            "callsign": callsign["callsign"],
            "atsu": "EGKK"}

    def test_dlic_aircraft_logoff(self, client: TestClient):
        """
        Test that an aircraft can log off using the logoff code from logon.
        """
        callsign = CallsignFactory()
        aircraft: ApiKey = UserApiKeyFactory()
        login_data: dict = {
            "logon_from": callsign["callsign"],
            "logon_to": "EGKK",
            "network": "vatsim",
            "created": dt.now(tz.utc).timestamp(),
            "logoff_code": "",
            "fans_1_a_atn_b1": False,
            "atn_b1": False,
            "fans_1_a": False
        }

        client.headers.update({"x-key": aircraft.api_key})

        # Logon first
        with patch(
            "acars_server.api.routes.dlic.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response = client.post("/dlic/aircraft/logon", json=login_data)

        assert response.status_code == 200
        obj = DataLinkInitiationCapability.model_validate(response.json()["data"])
        logoff_code = obj.logoff_code
        print(f"Logoff code: {obj}")

        # Logoff using the returned logoff_code
        logoff_data: dict = {
            "logoff_code": logoff_code
        }
        response = client.post("/dlic/logoff", json=logoff_data)
        print(f"Logoff response: {response.json()}")

        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json()["status"] == "logged off"
        assert response.json()["callsign"] == callsign["callsign"]
