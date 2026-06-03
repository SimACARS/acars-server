"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
import secrets
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse, parse_qs

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from tests.api.api_v1.test_dlic import dlic_logon_request
from tests.factories.user import CidFactory

def test_add_new_vatsim_user(client: TestClient):
    """Test to add a new user"""
    response = client.get("/user/new/vatsim")

    # Check if a redirect happened
    for rh in response.history:
        assert rh.status_code == 307

    # Parse the redirct url
    parsed = urlparse(str(response.url))
    query = parse_qs(parsed.query)
    print(query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.vatsim.net"
    assert parsed.path == "/oauth/authorize"
    assert query["response_type"][0] == "code"
    assert re.fullmatch(r"\d+", query["client_id"][0])
    assert query["redirect_uri"][0] == "https://efps.vnpas.uk/oauth/token/"
    assert re.fullmatch(r"[a-f0-9]+", query["state"][0])
    assert query["prompt"][0] == "login"

@patch("acars_server.api.routes.users.auth.VatsimAuth")
def test_callback(
    mock_vatsim_auth_class,
    client: TestClient
    ):
    """Test the callback with a login attempt"""
    cid = CidFactory()
    mock_vatsim_auth = MagicMock()
    mock_vatsim_auth_class.return_value = mock_vatsim_auth

    # ---- mock get_access_token ----
    mock_vatsim_auth.get_access_token.return_value = (
        200,
        {"access_token": secrets.token_hex(32)}
    )

    # ---- mock get_user_details ----
    mock_vatsim_auth.get_user_details.return_value = (
        200,
        {
            "data": {
                "cid": cid["cid"]
            }
        }
    )

    response_a = client.get(
        f"/callback/oauth/vatsim/{secrets.token_hex(16)}/{secrets.token_hex(32)}")

    assert response_a.status_code == 200
    assert response_a.json()["status"] == "user created"

    # Attempt to logon using the API key
    response_b, _ = dlic_logon_request(
        logon_from="RFI221B",
        logon_to="EGKK",
        api_key=response_a.json()["api_key"],
        endpoint="/dlic/aircraft/logon",
        client=client)

    assert response_b.status_code == 200
    assert response_b.json()["status"] == "logged on"
