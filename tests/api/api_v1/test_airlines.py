"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
import secrets
import threading
from time import sleep
from unittest.mock import AsyncMock, patch

# Third Party Libraries
import pytest
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import AirlineApiKey, ApiKey, RequestNewAirline
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.messages import MessageFactory, MessageFactoryNoCommit
from tests.factories.airlines import AirlineApiKeyFactory, NewAirlineRequestFactory
from tests.factories.user import CallsignFactory, UserApiKeyFactory

class TestTransmitMessage:
    """Airline Transmit Message"""
    def test_tx(self, client: TestClient):
        """
        Test that an airline can send a message to online aircraft
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()
        aircraft: ApiKey = UserApiKeyFactory()
        callsign = CallsignFactory()

        # Logon Aircraft
        response_ac, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft.api_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        # Check the results
        assert response_ac.status_code == 200

        # Logon Airline
        response_coy, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        print(response_coy.json())
        assert response_coy.status_code == 200

        # Don't attempt to validate message at this point
        # Message validation during post to endpoint
        message = MessageFactory(
            msg_to = callsign["callsign"],
            msg_from = airline.airline_callsign
            )

        client.headers.update({"x-key": airline.api_key})
        response = client.post("/airline/tx", json=message.model_dump())
        client.headers.pop("x-key")
        print(response.json())
        assert response.status_code == 201

    def test_tx_recipient_offline(self, client: TestClient):
        """
        Test that an airline attempting to send a message to an offline
        airline is rejected
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()
        callsign = CallsignFactory()

        # Logon Airline
        response_coy, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        print(response_coy.json())
        assert response_coy.status_code == 200

        # Don't attempt to validate message at this point
        # Message validation during post to endpoint
        message = MessageFactory(
            msg_to = callsign["callsign"],
            msg_from = airline.airline_callsign
            )

        client.headers.update({"x-key": airline.api_key})
        response = client.post("/airline/tx", json=message.model_dump())
        client.headers.pop("x-key")
        print(response.json())
        assert response.status_code == 404
        assert response.json()["error"] == f"{callsign['callsign']} is not active on the network"

    def test_tx_incorrect_airline(self, client: TestClient):
        """
        Test that an airline attempting to send a message to an offline
        airline is rejected
        """
        # Create the database entry
        airline: AirlineApiKey = AirlineApiKeyFactory()
        callsign = CallsignFactory()

        # Logon Airline
        response_coy, _ = dlic_logon_request(
            logon_from=airline.airline_callsign,
            logon_to="_SYSTEM_DLIC",
            api_key=airline.api_key,
            endpoint="/dlic/airline/logon",
            client=client
        )

        # Check the results
        print(response_coy.json())
        assert response_coy.status_code == 200

        # Don't attempt to validate message at this point
        # Message validation during post to endpoint
        message = MessageFactory(
            msg_to = callsign["callsign"],
            msg_from = airline.airline_callsign
            )

        client.headers.update({"x-key": airline.api_key})
        response = client.post("/airline/tx", json=message.model_dump())
        client.headers.pop("x-key")
        print(response.json())
        assert response.status_code == 404
        assert response.json()["error"] == f"{callsign['callsign']} is not active on the network"


class TestNewAirline:
    """Test creating a new airline"""
    def test_new(self, client: TestClient):
        """Create a new airline"""
        airline = NewAirlineRequestFactory()

        response = client.post("/airline/new", json=airline.model_dump())

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "/airline/domain_auth" in response.text

    def test_new_already_exists(self, client: TestClient):
        """Attempt to a create a new airline that already exists"""
        # This should create an airline
        airline_a: AirlineApiKey = AirlineApiKeyFactory()

        # This should create a request for the same airline
        airline_b: RequestNewAirline = NewAirlineRequestFactory(
            airline_callsign=airline_a.airline_callsign.split("_")[2],
            network=airline_a.network
            )

        response = client.post("/airline/new", json=airline_b.model_dump())
        assert response.status_code == 403
        assert response.json()["error"] == (f"{airline_b.airline_callsign} already "
                                            f"exists and is controlled by {airline_b.domain}")

    def test_new_request_already_made(self, client: TestClient):
        """Create a new airline"""
        airline: RequestNewAirline = NewAirlineRequestFactory()

        # First request to create an airline
        response_a = client.post("/airline/new", json=airline.model_dump())
        assert response_a.status_code == 200

        # Second request to create the same airline
        response_b = client.post("/airline/new", json=airline.model_dump())
        assert response_b.status_code == 403
        assert response_b.json()["error"] == ("Request already exists")
        assert response_b.json()["data"]["network"] == airline.network
        assert response_b.json()["data"]["airline_name"] == airline.airline_name
        assert response_b.json()["data"]["airline_callsign"] == airline.airline_callsign
        assert response_b.json()["data"]["domain"] == airline.domain

    @patch("acars_server.api.routes.airlines.Resolver.resolve")
    def test_new_with_domain_verification(self, mock_resolve, client: TestClient):
        """Create a new airline"""
        airline: RequestNewAirline = NewAirlineRequestFactory(domain="NOT-A-DOMAIN.LOCAL")

        response = client.post("/airline/new", json=airline.model_dump())
        assert response.status_code == 200

        html_search = re.search(r"\"acars-verify-([A-Za-z0-9\_\-]+)\"", str(response.text))
        if html_search:
            verification_token = html_search.group(1)
            print(verification_token)

            mock_resolve.return_value = [
                f"acars-verify-{str(verification_token)}"
            ]

            response_b = client.get(f"/airline/domain_auth/{verification_token}")
            print(response_b.content)
            print(response_b.json())
            assert response_b.status_code == 200
            assert re.match(r"[a-zA-Z0-9]{64}", response_b.json()["api_key"])
        else:
            pytest.fail(f"Couldn't find verification token in {str(response.text)}")

    def test_auth_bad_verification_token(self, client: TestClient):
        """Passes a bad verification token"""
        verification_token = secrets.token_urlsafe(32) 
        response = client.get(f"/airline/domain_auth/{verification_token}")
        assert response.status_code == 404
        assert response.json()["error"] == ("verification token not recognised")

    @patch("acars_server.api.routes.airlines.Resolver.resolve")
    def test_auth_with_no_matching_txt_record(self, mock_resolve, client: TestClient):
        """Create a new airline"""
        airline: RequestNewAirline = NewAirlineRequestFactory(domain="NOT-A-DOMAIN.LOCAL")

        response = client.post("/airline/new", json=airline.model_dump())
        assert response.status_code == 200

        html_search = re.search(r"\"acars-verify-([A-Za-z0-9\_\-]+)\"", str(response.text))
        if html_search:
            verification_token = html_search.group(1)
            print(verification_token)

            mock_resolve.return_value = [
                f"this-is-wrong-{str(verification_token)}"
            ]

            response_b = client.get(f"/airline/domain_auth/{verification_token}")

            assert response_b.status_code == 404
            assert response_b.json()["error"] == ("no matching TXT record was found")
        else:
            pytest.fail(f"Couldn't find verification token in {str(response.text)}")


class TestAirlineRx:
    """Test Airline Rx Path"""

    @pytest.mark.asyncio
    async def test_valid_auth(self, client: TestClient):
        company: AirlineApiKey = AirlineApiKeyFactory()
        aircraft: ApiKey = UserApiKeyFactory()
        callsign = CallsignFactory()

        url = f"/airline/rx/{company.network}/{company.airline_callsign[-3:]}"

        def message():
            # Login
            dlic_logon_request(
                logon_from=callsign["callsign"],
                logon_to="EGKK",
                api_key=aircraft.api_key,
                endpoint="/dlic/aircraft/logon",
                client=client
            )
    
            message = MessageFactoryNoCommit(
                msg_from=callsign["callsign"],
                msg_to=company.airline_callsign)
    
            client.headers.update({"x-key": aircraft.api_key})
            with patch(
                "acars_server.api.routes.acars.callsign_verification",
                new=AsyncMock(return_value=callsign["callsign"])
            ):
                while True:
                    sleep(2)
                    client.post("/acars/tx", json=message.model_dump())
            client.headers.pop("x-key")
        thread = threading.Thread(target=message, daemon=True)
        thread.start()

        client.headers.update({"x-key": company.api_key})

        # 1. start SSE stream FIRST
        async with client.stream("GET", url) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")

            async for line in response.aiter_lines():
                print(line)

                if line.startswith("data:"):
                    assert "expected_value" in line
                    break


    def test_invalid_auth(self, client: TestClient):
        """Test an invalid api key"""
        client.headers.update({"x-key": "NOT_A_KEY"})
        response = client.get("/airline/rx/vatsim/wiffle")
        assert response.status_code == 401
