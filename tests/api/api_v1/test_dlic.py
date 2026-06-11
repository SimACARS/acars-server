"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import re
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime as dt, timezone as tz
from unittest.mock import AsyncMock, patch

# Third Party Libraries
import jwt
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.api.services.auth_services import JWTAuth
from acars_server.databases import AirlineApiKey, DataLinkInitiationCapability
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import CallsignFactory
from tests.fixtures.airline_authorisation import create_airline_api_key
from tests.fixtures.auth import Authentication
from tests.fixtures.user_authorisation import create_api_key

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
jwt_auth = JWTAuth()

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


class TestAirlineLogon:
    """Airline Logon"""
    def test_dlic_airline_logon(self, client: TestClient):
        """
        Test that an aircraft can log on using the API key authentication.
        """
        airline = Authentication(client, "airline")
        airline_logon_response = airline.logon()
        print(airline_logon_response.json())

        # Check the results
        assert airline_logon_response.status_code == 200
        assert airline_logon_response.json()["status"] == "logged on"
        obj = DataLinkInitiationCapability.model_validate(airline_logon_response.json()["data"])
        assert obj
        assert re.fullmatch(r"\d+\.\d+", str(obj.created))
        assert obj.logon_from == f"_COY_{airline.info['callsign']}"
        assert obj.logon_to == "_SYSTEM_DLIC"
        assert obj.network == "vatsim"
        assert obj.fans_1_a_atn_b1 is False
        assert obj.atn_b1 is False
        assert obj.fans_1_a is False
        assert re.fullmatch(r"[a-f0-9]{64}", obj.logoff_code)
        assert obj.logoff_code == airline_logon_response.json()["data"]["logoff_code"]

    def test_dlic_airline_logon_duplicate(self, client: TestClient):
        """
        Test that a duplicate airline cannot log on using the API key authentication.
        """
        # Create the database entry
        airline, airline_key = create_airline_api_key()

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline_key,
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
        airline, airline_key = create_airline_api_key()

        # Login
        response, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline_key,
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
        client.headers.update({"x-key": airline_key})
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
        airline_a: AirlineApiKey = AirlineApiKeyFactory() # type: ignore
        airline_b: AirlineApiKey = AirlineApiKeyFactory() # type: ignore

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
        _, key = create_api_key()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200
        assert jwt.decode(
                jwt=response.json()["access_token"],
                key=str(JWT_SECRET),
                audience=["acars:aircraft"],
                options={
                    "require": [
                        "exp",
                        "nbf",
                        "iat",
                        "iss",
                        "aud",
                        "network",
                        "loc",
                        "uid",
                        "sub",
                        "jti"
                    ]
                    },
                algorithms=[str(JWT_ALGORITHM)]
                )
        assert response.json()["token_type"] == "bearer"

    def test_dlic_aircraft_logon_duplicate(self, client: TestClient):
        """
        Test that a duplicate callsign cannot log on using the API key authentication.
        """
        # Create the database entry
        _, key_a = create_api_key()
        _, key_b = create_api_key()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key_a,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key_b,
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
        _, key = create_api_key()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200
        jwtt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwtt}"})

        # Logoff using the returned logoff_code
        response = client.post("/dlic/aircraft/logoff")
        print(f"Logoff response: {response.json()}")
        client.headers.pop("Authorization")

        assert response.status_code == 200
        assert response.json()["status"] == "logged off"
        assert response.json()["callsign"] == callsign["callsign"]

    @pytest.mark.anyio
    async def test_dlic_aircraft_incorrect_logoff(self, client: TestClient):
        """
        Test that an incorrect logoff code is rejected.
        """
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200
        jwtt = response.json()["access_token"]
        signature = str(jwtt).split(".")
        jwt_a = {
            "scheme": "bearer",
            "credentials": jwtt
        }
        jwt_b = HTTPAuthorizationCredentials.model_validate(jwt_a)

        # Adjust JWT contents
        jwtd = await jwt_auth.decode_jwt(jwt_b, ["acars:aircraft"])
        jwtd["loc"] = secrets.token_hex(32)
        data_block = urlsafe_b64encode(str(jwtd).encode()).decode()
        jwt_encoded = str(f"{signature[0]}.{data_block}.{signature[2]}")

        client.headers.update({"Authorization": f"Bearer {jwt_encoded}"})

        response = client.post("/dlic/aircraft/logoff")
        client.headers.pop("Authorization")

        assert response.status_code == 401

    def test_dlic_aircraft_incorrect_station_type(self, client: TestClient):
        """
        Test that an incorrect station_type is rejected.
        """
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()

        # Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response.status_code == 200

        # Logoff using the incorret logoff_code
        logoff_data: dict = {
            "logoff_code": secrets.token_hex(32)
        }
        client.headers.update({"x-key": key})
        response = client.post("/dlic/wiffle/logoff", json=logoff_data)
        print(f"Logoff response: {response.json()}")
        client.headers.pop("x-key")

        assert response.status_code == 404
