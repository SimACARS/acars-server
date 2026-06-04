"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import AirlineApiKey, ApiKey
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.messages import MessageFactory
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
            msg_from = f"_COY_{airline.airline_callsign}"
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
            msg_from = f"_COY_{airline.airline_callsign}"
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
            msg_from = f"_COY_{airline.airline_callsign}"
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
        airline_a: AirlineApiKey = AirlineApiKeyFactory()
        airline_b = NewAirlineRequestFactory(
            airline_callsign=airline_a.airline_callsign,
            network=airline_a.network
            )
        response = client.post("/airline/new", json=airline_b.model_dump())
        assert response.status_code == 403
        assert response.json()["error"] == (f"{airline_b.airline_callsign} already "
                                            f"exists and is controlled by {airline_b.domain}")

    def test_new_request_already_made(self, client: TestClient):
        """Create a new airline"""
        airline = NewAirlineRequestFactory()

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
