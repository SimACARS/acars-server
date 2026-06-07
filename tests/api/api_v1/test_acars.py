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
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.messages import MessageFactory
from tests.factories.user import CallsignFactory
from tests.fixtures.user_authorisation import create_api_key

class TestAircraftAcarsPoll:
    """Aircraft Poll"""
    def test_poll_aircraft_no_messages(self, client: TestClient):
        """
        Test that an aircraft can poll the system
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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
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
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()
        messages: StoreAndForward = MessageFactory(msg_to=callsign["callsign"])
        i = 0
        while i < 100:
            MessageFactory()
            i += 1

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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response_b = client.post("/acars/poll")
        client.headers.pop("Authorization")

        rjson = response_b.json()
        assert response_b.status_code == 200
        assert rjson["message_count"] == 1
        assert rjson["messages"][0]["msg_from"] == messages.msg_from
        assert rjson["messages"][0]["msg_to"] == callsign["callsign"]
        assert rjson["messages"][0]["msg_type"] == messages.msg_type
        assert rjson["messages"][0]["packet"] == messages.packet
        assert rjson["messages"][0]["network"] == messages.network

    def test_poll_aircraft_with_no_callsign(self, client: TestClient):
        """
        Test what happens when no callsign is returned
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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
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
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()
        message: StoreAndForward = MessageFactory(msg_from=callsign["callsign"])

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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response_b = client.post("/acars/tx", json=message.model_dump())
        client.headers.pop("Authorization")

        assert response_b.status_code == 201

    def test_send_message_no_callsign(self, client: TestClient):
        """Tests sending a message"""
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()
        message: StoreAndForward = MessageFactory(msg_from=callsign["callsign"])

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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=None)):

            response_b = client.post("/acars/tx", json=message.model_dump())
        client.headers.pop("Authorization")

        assert response_b.status_code == 403

    def test_legacy_send_message(self, client: TestClient):
        """Tests sending a message"""
        # Create the database entry
        _, key = create_api_key()
        callsign = CallsignFactory()
        message: StoreAndForward = MessageFactory(msg_from=callsign["callsign"])

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
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})

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
