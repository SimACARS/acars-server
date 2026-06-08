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
from datetime import datetime as dt, timezone as tz
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse, parse_qs

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import ATSUAuthorisedCallsign
from tests.factories.atsu import ATSUAuthorisedCallsignFactory
from tests.factories.user import CidFactory, OAuthStateFactory

def atsu_dlic_logon_request(
    logon_from:str,
    endpoint:str,
    client: TestClient):
    """Generate a DLIC logon request"""
    logon_data: dict = {
            "logon_from": logon_from,
            "logon_to": "_SYSTEM_DLIC",
            "network": "vatsim",
            "created": dt.now(tz.utc).timestamp(),
            "logoff_code": "",
            "fans_1_a_atn_b1": False,
            "atn_b1": False,
            "fans_1_a": False
        }
    response = client.post(endpoint, json=logon_data)

    return response, logon_data


class TestATSULogon:
    """ATSU Logon"""
    def test_atsu_logon(self, client: TestClient):
        """Test to add a new user"""
        atsu_data: ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()
        response, _ = atsu_dlic_logon_request(
            logon_from=atsu_data.callsign,
            endpoint="/dlic/atsu/logon",
            client=client
        )

        # Check if a redirect happened
        for rh in response.history:
            assert rh.status_code == 307

        # Parse the redirct url
        parsed = urlparse(str(response.url))
        query = parse_qs(parsed.query)

        assert parsed.scheme == "https"
        assert parsed.netloc == "auth.vatsim.net"
        assert parsed.path == "/oauth/authorize"
        assert query["response_type"][0] == "code"
        assert re.fullmatch(r"\d+", query["client_id"][0])
        assert query["redirect_uri"][0] == os.getenv("VATSIM_OAUTH_REDIRECT_URI_ATSU")
        assert re.fullmatch(r"[a-f0-9]+", query["state"][0])
        assert query["prompt"][0] == "none"

    def test_atsu_invalid_network(self, client: TestClient):
        """Test that an invalid network is rejected"""
        response = client.get("/user/new/wiffle")
        assert response.status_code == 400

    def test_atsu_valid_network_no_oauth(self, client: TestClient):
        """Test that an invalid network is rejected"""
        response = client.get("/user/new/poscon")
        assert response.status_code == 400
