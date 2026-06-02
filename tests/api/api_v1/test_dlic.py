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

def dlic_logon_request(
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
    client.headers.update({"x-key": api_key})
    with patch(
        "acars_server.api.routes.dlic.callsign_verification",
        new=AsyncMock(return_value=logon_from)
    ):
        response = client.post(endpoint, json=logon_data)
    client.headers.pop("x-key")

    return response, logon_data


class TestAirlineLogon:
    """Airline Logon"""
    def test_dlic_airline_logon(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()

        # Login
        response, login_data = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
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

    def test_dlic_airline_logon_duplicate(self, client: TestClient):
        """
        Test that a duplicate airline cannot log on using the API key authentication.
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results

        assert response.status_code == 200
        assert response.json() == {
            "status": "already logged on",
            "callsign": airline.airline_callsign,
            "atsu": "_SYSTEM_DLIC"}

    def test_dlic_airline_logoff(self, client: TestClient):
        """
        Test that an airline can log off using the logoff code from logon.
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200
        obj = DataLinkInitiationCapability.model_validate(response.json()["data"])
        logoff_code = obj.logoff_code
        print(f"Logoff code: {obj}")

        # Logoff using the returned logoff_code
        logoff_data: dict = {
            "logoff_code": logoff_code
        }
        client.headers.update({"x-key": airline.api_key})
        response = client.post("/dlic/airline/logoff", json=logoff_data)
        print(f"Logoff response: {response.json()}")
        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json()["status"] == "logged off"
        assert response.json()["callsign"] == f"_COY_{airline.airline_callsign}"

    def test_dlic_airline_incorrect_callsign(self, client: TestClient):
        """
        Test that an airline can log off using the logoff code from logon.
        """
        # Create the database entry
        airline_a: AirlineApiKey = AirlineApiKeyFactory()
        airline_b: AirlineApiKey = AirlineApiKeyFactory()
        print(f"AIRLINE A: {airline_a}")
        print(f"AIRLINE B: {airline_b}")

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline_b.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline_a.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 401

class TestAircraftLogon:
    """Aircraft Logon"""
    def test_dlic_aircraft_logon(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        # Create the database entry
        aircraft: ApiKey = UserApiKeyFactory()
        callsign = CallsignFactory()

        # Login
        response, login_data = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft.api_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
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
        Test that a duplicate callsign cannot log on using the API key authentication.
        """
        # Create the database entry
        aircraft: ApiKey = UserApiKeyFactory()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft.api_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft.api_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results

        assert response.status_code == 200
        assert response.json() == {
            "status": "already logged on",
            "callsign": callsign["callsign"],
            "atsu": "EGKK"}

    def test_dlic_aircraft_logoff(self, client: TestClient):
        """
        Test that an aircraft can log off using the logoff code from logon.
        """
        # Create the database entry
        aircraft: ApiKey = UserApiKeyFactory()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft.api_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200
        obj = DataLinkInitiationCapability.model_validate(response.json()["data"])
        logoff_code = obj.logoff_code
        print(f"Logoff code: {obj}")

        # Logoff using the returned logoff_code
        logoff_data: dict = {
            "logoff_code": logoff_code
        }
        client.headers.update({"x-key": aircraft.api_key})
        response = client.post("/dlic/aircraft/logoff", json=logoff_data)
        print(f"Logoff response: {response.json()}")
        client.headers.pop("x-key")

        assert response.status_code == 200
        assert response.json()["status"] == "logged off"
        assert response.json()["callsign"] == callsign["callsign"]
