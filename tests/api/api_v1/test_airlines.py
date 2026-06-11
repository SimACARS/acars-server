"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
import secrets
from unittest.mock import AsyncMock, patch

# Third Party Libraries
import httpx
import pytest
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import AirlineApiKey, RequestNewAirline, redis_async_db
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.messages import MessageFactory, MessageFactoryNoCommit
from tests.factories.airlines import AirlineApiKeyFactory, NewAirlineRequestFactory
from tests.factories.user import CallsignFactory
from tests.fixtures.airline_authorisation import create_airline_api_key
from tests.fixtures.auth import Authentication
from tests.fixtures.user_authorisation import create_api_key

class TestTransmitMessage:
    """Airline Transmit Message"""
    def test_tx(self, client: TestClient):
        """
        Test that an airline can send a message to online aircraft
        """
        airline = Authentication(client, "airline")
        airline.logon()

        aircraft = Authentication(client, "aircraft")
        aircraft.logon()

        # Don't attempt to validate message at this point
        # Message validation during post to endpoint
        message = MessageFactory(
            msg_to = aircraft.info["callsign"],
            msg_from = airline.info["callsign"]
            )

        client.headers.update(airline.info["headers"])
        response = client.post("/airline/tx", json=message.model_dump())
        client.headers.pop("x-key")
        print(response.json())
        assert response.status_code == 201

    def test_tx_recipient_offline(self, client: TestClient):
        """
        Test that an airline attempting to send a message to an offline
        airline is rejected
        """
        airline = Authentication(client, "airline")
        airline.logon()

        callsign = CallsignFactory()

        # Don't attempt to validate message at this point
        # Message validation during post to endpoint
        message = MessageFactory(
            msg_to = callsign["callsign"],
            msg_from = airline.info["callsign"]
            )

        client.headers.update(airline.info["headers"])
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
        """Test valid authentication"""
        airline = Authentication(client, "airline")
        airline.logon()

        aircraft = Authentication(client, "aircraft")
        aircraft.logon()

        url = f"/airline/rx/{airline.airline.network}/{airline.airline.airline_callsign[-3:]}"

        msg = MessageFactoryNoCommit(
            msg_from=aircraft.info["callsign"],
            msg_to=airline.info["callsign"])

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=aircraft.info["callsign"])
        ):
            response_tx = client.post("/acars/tx", json=msg.model_dump())
        client.headers.pop("Authorization")

        assert response_tx.status_code == 201
        print("INFO: sent tx", response_tx.status_code)

        client.headers.update(airline.info["headers"])
        print("INFO: opening stream", url)

        # Mock Redis to avoid event loop issues in testing
        # Return a sample message after first xread call
        try:
            airline_callsign = f"_COY_{airline.airline.airline_callsign[-3:]}"
            msg_data = {
                b"msg_from": aircraft.info["callsign"].encode() if isinstance(
                    aircraft.info["callsign"], str) else aircraft.info["callsign"],
                b"msg_to": airline_callsign.encode() if isinstance(
                    airline_callsign, str) else airline_callsign,
                b"msg_type": b"telex",
                b"packet": b"TEST",
                b"network": b"vatsim",
            }

            # Mock the xrange and xread calls
            old_xrange = redis_async_db.xrange
            old_xread = redis_async_db.xread

            async def mock_xrange(*args, **kwargs):
                return []

            call_count = [0]
            async def mock_xread(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] == 1:
                    # Return message on first call
                    return [
                        [f"msg:coy:vatsim:_COY_{format(airline.airline.airline_callsign[-3:]).encode()}",
                         [("1-0", msg_data)]]]
                else:
                    # No more messages
                    return None

            redis_async_db.xrange = mock_xrange
            redis_async_db.xread = mock_xread

            # Use httpx client directly to bypass TestClient streaming limitations
            transport = httpx.ASGITransport(app=client.app)
            async_client = httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000")
            async_client.headers.update(airline.info["headers"])

            print("INFO: about to call async stream")

            async with async_client.stream("GET", url) as response:
                print("INFO: stream opened", response.status_code)
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")

                found = False
                async for line in response.aiter_lines():
                    print(line)

                    if line.startswith("data:"):
                        found = True
                        assert aircraft.info["callsign"] in line
                        break

                assert found, "No data message received from SSE stream"

            await async_client.aclose()
        finally:
            # Restore original Redis methods
            redis_async_db.xrange = old_xrange
            redis_async_db.xread = old_xread

    def test_invalid_auth(self, client: TestClient):
        """Test an invalid api key"""
        client.headers.update({"x-key": "NOT_A_KEY"})
        response = client.get("/airline/rx/vatsim/wiffle")
        assert response.status_code == 401
