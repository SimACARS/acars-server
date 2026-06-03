"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
import secrets
from datetime import datetime as dt, timezone as tz
from unittest.mock import AsyncMock, patch

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import AirlineApiKey, ApiKey, DataLinkInitiationCapability
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import CallsignFactory, UserApiKeyFactory

class TestAircraftAcars:
    """Aircraft Logon"""
    def test_poll_aircraft_no_messages(self, client: TestClient):
        """
        Test that an aircraft can poll the system
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

        client.headers.update({"x-key": aircraft.api_key})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response_b = client.post("/acars/poll")
        client.headers.pop("x-key")
        print(response_b.json())
        assert response_b.status_code == 200
        assert response_b.json()["msg_count"] == 0
