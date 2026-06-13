"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from unittest.mock import AsyncMock, patch

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import StoreAndForward
from tests.factories.messages import MessageFactory
from tests.fixtures.auth import Authentication

class TestAircraftAcarsPoll:
    """Aircraft Poll"""
    def test_poll_aircraft_no_messages(self, client: TestClient):
        """
        Test that an aircraft can poll the system
        """
        aircraft = Authentication(client, "aircraft")
        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=aircraft.info["callsign"])
        ):
            response_b = client.post("/acars/poll")
        client.headers.pop("Authorization")
        print(response_b.json())
        assert response_b.status_code == 200
        assert response_b.json()["msg_count"] == 0

    def test_poll_aircraft_with_messages(self, client: TestClient):
        """
        Test that an aircraft can poll the system and retrieve messages
        """
        aircraft = Authentication(client, "aircraft")

        messages: StoreAndForward = MessageFactory(msg_to=aircraft.info["callsign"]) # type: ignore
        i = 0
        while i < 100:
            MessageFactory()
            i += 1

        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=aircraft.info["callsign"])
        ):
            response_b = client.post("/acars/poll")
        client.headers.pop("Authorization")

        rjson = response_b.json()
        assert response_b.status_code == 200
        assert rjson["message_count"] == 1
        assert rjson["messages"][0]["msg_from"] == messages.msg_from
        assert rjson["messages"][0]["msg_to"] == aircraft.info["callsign"]
        assert rjson["messages"][0]["msg_type"] == messages.msg_type
        assert rjson["messages"][0]["packet"] == messages.packet
        assert rjson["messages"][0]["network"] == messages.network

    def test_poll_aircraft_with_no_callsign(self, client: TestClient):
        """
        Test what happens when no callsign is returned
        """
        aircraft = Authentication(client, "aircraft")
        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=None)
        ):
            response_b = client.post("/acars/poll")
        client.headers.pop("Authorization")

        assert response_b.status_code == 403


class TestAircraftAcarsTx:
    """Aircraft Tx"""

    def test_send_message(self, client: TestClient):
        """Tests sending a message"""
        aircraft = Authentication(client, "aircraft")
        message: StoreAndForward = MessageFactory(msg_from=aircraft.info["callsign"]) # type: ignore
        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=aircraft.info["callsign"])
        ):
            response_b = client.post("/acars/tx/atn_vhf", json=message.model_dump())
        client.headers.pop("Authorization")

        assert response_b.status_code == 201

    def test_send_message_no_callsign(self, client: TestClient):
        """Tests sending a message"""
        aircraft = Authentication(client, "aircraft")
        message: StoreAndForward = MessageFactory(msg_from=aircraft.info["callsign"]) # type: ignore
        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=None)):

            response_b = client.post("/acars/tx/atn_vhf", json=message.model_dump())
        client.headers.pop("Authorization")

        assert response_b.status_code == 403

    def test_legacy_send_message(self, client: TestClient):
        """Tests sending a message"""
        aircraft = Authentication(client, "aircraft")
        message: StoreAndForward = MessageFactory(msg_from=aircraft.info["callsign"]) # type: ignore
        aircraft_logon_response = aircraft.logon()

        # Check the results
        assert aircraft_logon_response.status_code == 200

        client.headers.update(aircraft.info["headers"])

        msg = {
            "logon": "NoOp",
            "from": message.msg_from,
            "to": message.msg_to,
            "type": message.msg_type,
            "packet": message.packet
        }

        with patch(
            "acars_server.api.routes.acars.transmit_a_message",
            new=AsyncMock(return_value=None)):
            response = client.get("/acars/connect.html", params=msg)
        print(response.url)
        client.headers.pop("Authorization")

        assert response.status_code == 200
