"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import json
import os
import re
import secrets
from datetime import datetime as dt, timezone as tz
from typing import Dict, Tuple
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse, parse_qs

# Third Party Libraries
import httpx2
import pytest
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# Local Libraries
from acars_server import databases
from acars_server.api.services.atsu_services import complete_vatsim_atsu_logon
from acars_server.api.services.auth_services import jwt_auth
from tests.factories.atsu import ATSUAuthorisedCallsignFactory
from tests.factories.messages import MessageFactoryNoCommit
from tests.factories.user import CidFactory, OAuthStateFactory
from tests.fixtures.auth import Authentication

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

@pytest.fixture
def vatsim_oauth_response():
    """VATSIM OAuth Response"""
    cid = CidFactory()
    return (200, {"data": {"cid": cid["cid"],"vatsim": {"rating": {"id": 4}}}})


class VatsimAccessToken:
    """VATSIM Access Token"""
    def __init__(self, status_code:int=200) -> None:
        self.status_code = status_code
        self.state = OAuthStateFactory()
        self.access_token = secrets.token_hex(32)

    def token(self) -> Tuple[int, Dict[str,str]]:
        """Returns a token"""
        return (
            self.status_code,
                {
                    "access_token": self.access_token,
                    "state": self.state.oauth_state
                }
            )


class TestATSULogon:
    """ATSU Logon"""
    def test_atsu_dlic_logon(self, client: TestClient):
        """Test to add a new user"""
        atsu = Authentication(client, "atsu")
        atsu_logon_response = atsu.logon()

        # Check if a redirect happened
        for rh in atsu_logon_response.history:
            assert rh.status_code == 307

        # Parse the redirct url
        parsed = urlparse(str(atsu_logon_response.url))
        query = parse_qs(parsed.query)

        assert parsed.scheme == "https"
        assert parsed.netloc == "auth.vatsim.net"
        assert parsed.path == "/oauth/authorize"
        assert query["response_type"][0] == "code"
        assert re.fullmatch(r"\d+", query["client_id"][0])
        assert query["redirect_uri"][0] == os.getenv("VATSIM_OAUTH_REDIRECT_URI_ATSU")
        assert re.fullmatch(r"[a-f0-9]+", query["state"][0])
        assert query["prompt"][0] == "none"

    def test_atsu_dlic_invalid_network(self, client: TestClient):
        """Test that an invalid network is rejected"""
        response = client.get("/user/new/wiffle")
        assert response.status_code == 400

    def test_atsu_dlic_valid_network_no_oauth(self, client: TestClient):
        """Test that an invalid network is rejected"""
        response = client.get("/user/new/poscon")
        assert response.status_code == 400


class TestATSUCallback:
    """ATSU Callbacks"""
    @patch("acars_server.api.routes.callbacks.complete_vatsim_atsu_logon")
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    def test_callback(self,
        mock_vatsim_auth_class,
        mock_atsu_logon_func,
        vatsim_oauth_response,
        client: TestClient
        ):
        """Test the callback with a login attempt"""
        mock_atsu_logon = MagicMock()
        mock_vatsim_auth = MagicMock()

        mock_vatsim_auth_class.return_value = mock_vatsim_auth
        mock_atsu_logon_func.return_value = mock_atsu_logon

        # Mock get_access_token
        gat = VatsimAccessToken()
        mock_vatsim_auth.get_access_token.return_value = gat.token()

        # Mock get_user_details
        mock_vatsim_auth.get_user_details.return_value = vatsim_oauth_response

        # Mock get_access_token
        mock_atsu_logon.return_value = JSONResponse(
            status_code=200,
            content={"success": True},
        )

        response = client.get(
            f"/callback/oauth/vatsim/atsu/{gat.state.oauth_state}/{secrets.token_hex(32)}")
        print(response.json())
        assert response.status_code == 200

    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    def test_callback_no_access_token(self,
        mock_vatsim_auth_class,
        client: TestClient
        ):
        """Test the callback with a login attempt"""
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth

        state = OAuthStateFactory()

        # Mock get_access_token
        mock_vatsim_auth.get_access_token.return_value = (
            400,
            {"hint": "some hint from the oauth provider"}
        )

        response = client.get(
            f"/callback/oauth/vatsim/atsu/{state.oauth_state}/{secrets.token_hex(32)}")
        print(response.json())
        assert response.status_code == 400
        assert response.json()["error"] == "some hint from the oauth provider"

    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    def test_callback_no_user_details(self,
        mock_vatsim_auth_class,
        client: TestClient
        ):
        """Test the callback with a login attempt"""
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth

        # Mock get_access_token
        gat = VatsimAccessToken()
        mock_vatsim_auth.get_access_token.return_value = gat.token()

        # Mock get_user_details
        mock_vatsim_auth.get_user_details.return_value = (
            400,
            {"hint": "some hint from the oauth provider"}
        )

        response = client.get(
            f"/callback/oauth/vatsim/atsu/{gat.state.oauth_state}/{secrets.token_hex(32)}")
        print(response.json())
        assert response.status_code == 400
        assert response.json()["error"] == {"hint": "some hint from the oauth provider"}

    def test_callback_no_state_code(self, client: TestClient):
        """Tests a callback with no or invalid state code"""
        response = client.get(
            f"/callback/oauth/vatsim/atsu/{secrets.token_hex(32)}/{secrets.token_hex(32)}")
        assert response.status_code == 404
        assert response.json()["error"] == "State code not found"

    @patch("acars_server.api.routes.callbacks.complete_vatsim_atsu_logon")
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    def test_callback_duplicate_state_code(self,
        mock_vatsim_auth_class,
        mock_atsu_logon_func,
        vatsim_oauth_response,
        client: TestClient
        ):
        """Tests a callback with duplicate state code"""
        mock_atsu_logon = MagicMock()
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth
        mock_atsu_logon_func.return_value = mock_atsu_logon

        # Mock get_access_token
        gat = VatsimAccessToken()
        mock_vatsim_auth.get_access_token.return_value = gat.token()

        # Mock get_user_details
        mock_vatsim_auth.get_user_details.return_value = vatsim_oauth_response

        # Mock get_access_token
        mock_atsu_logon.return_value = JSONResponse(
            status_code=200,
            content={"success": True},
        )

        response_a = client.get(
            f"/callback/oauth/vatsim/atsu/{gat.state.oauth_state}/{secrets.token_hex(32)}")

        assert response_a.status_code == 200

        response_b = client.get(
            f"/callback/oauth/vatsim/atsu/{gat.state.oauth_state}/{secrets.token_hex(32)}")

        assert response_b.status_code == 404
        assert response_b.json()["error"] == "State code not found"


class TestATSUCompleteLogon:
    """ATSU Complete Logon"""

    @pytest.mark.asyncio
    @patch("acars_server.api.services.atsu_services.callsign_verification",
           new_callable=AsyncMock)
    async def test_complete_vatsim_atsu_logon(
        self,
        mock_callsign_verification_func,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""

        atsu = Authentication(None, "atsu")

        mock_callsign_verification_func.return_value = atsu.info["callsign"]

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)
        rdata = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        vdata = HTTPAuthorizationCredentials.model_validate(rdata)

        assert await jwt_auth.decode_jwt(vdata, ["acars:atsu"])

    @pytest.mark.asyncio
    async def test_complete_vatsim_atsu_logon_incorrect_rating(self, db, vatsim_oauth_response):
        """Complete VATSIM ATSU Logon with incorrect rating"""
        vor = vatsim_oauth_response
        vor[1]["data"]["vatsim"]["rating"]["id"] = 1

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)

        assert response.status_code == 403
        assert json.loads(response.body)["error"] == "No ATC rating found"

    @pytest.mark.asyncio
    @patch("acars_server.api.services.atsu_services.callsign_verification",
           new_callable=AsyncMock)
    async def test_complete_vatsim_atsu_logon_unlinked_callsign(
        self,
        mock_callsign_verification_func,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""

        ATSUAuthorisedCallsignFactory()

        mock_callsign_verification_func.return_value = "NOT_A_CALLSIGN"

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)

        assert response.status_code == 404
        assert json.loads(
            response.body)["error"] == "NOT_A_CALLSIGN is not linked to an ATSU callsign"

    @pytest.mark.asyncio
    @patch("acars_server.api.services.atsu_services.callsign_verification",
           new_callable=AsyncMock)
    async def test_complete_vatsim_atsu_logon_duplicate_callsign(
        self,
        mock_callsign_verification_func,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""

        atsu = Authentication(None, "atsu")

        mock_callsign_verification_func.return_value = atsu.info["callsign"]

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)
        rdata = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        vdata = HTTPAuthorizationCredentials.model_validate(rdata)

        assert await jwt_auth.decode_jwt(vdata, ["acars:atsu"])

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)
        data = json.loads(response.body)
        assert response.status_code == 200
        assert data["status"] == "already logged on"


class TestATSURx:
    """Test ATSU Rx Path"""

    @pytest.mark.skip("Incomplete coding")
    @pytest.mark.anyio
    @patch("acars_server.api.routes.callbacks.complete_vatsim_atsu_logon")
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    async def test_valid_auth(
        self,
        mock_vatsim_auth_class,
        mock_callsign_verification_func,
        client: TestClient,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth

        # ATSU Generator
        mock_vatsim_auth.get_user_details.return_value = vatsim_oauth_response
        atsu_data: databases.ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()
        mock_callsign_verification_func.return_value = atsu_data.callsign
        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)
        print(json.loads(response.body))

        atsu_auth_headers = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        atsu_url = f"/atsu/rx/{atsu_data.network}/{atsu_data.callsign}"

        # Aircraft Generator
        _, aircraft_key = create_api_key()
        callsign = CallsignFactory()

        # Aircraft Login
        response, _ = dlic_logon_request(
            logon_from=callsign["callsign"],
            logon_to="EGKK",
            api_key=aircraft_key,
            endpoint="/dlic/aircraft/logon",
            client=client
        )

        msg = MessageFactoryNoCommit(
            msg_from=callsign["callsign"],
            msg_to=atsu_data.callsign)

        # Aircraft Send Message
        assert response.status_code == 200
        jwt = response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {jwt}"})
        with patch(
            "acars_server.api.routes.acars.callsign_verification",
            new=AsyncMock(return_value=callsign["callsign"])
        ):
            response_tx = client.post("/acars/tx", json=msg.model_dump())
        client.headers.pop("Authorization")

        assert response_tx.status_code == 201
        print("INFO: sent tx", response_tx.status_code)

        # Mock Redis to avoid event loop issues in testing
        # Return a sample message after first xread call
        try:
            msg_data = {
                b"msg_from": callsign["callsign"].encode() if isinstance(
                    callsign["callsign"], str) else callsign["callsign"],
                b"msg_to": atsu_data.callsign.encode() if isinstance(
                    atsu_data.callsign, str) else atsu_data.callsign,
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
                        [f"msg:atc:vatsim:{format(atsu_data.callsign).encode()}",
                         [("1-0", msg_data)]]]
                else:
                    # No more messages
                    return None

            redis_async_db.xrange = mock_xrange
            redis_async_db.xread = mock_xread

            # Use httpx client directly to bypass TestClient streaming limitations
            transport = httpx2.ASGITransport(app=client.app)
            async_client = httpx2.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000")
            async_client.headers.update({"Authorization": f"Bearer {atsu_auth_headers['credentials']}"})

            print("INFO: about to call async stream")

            async with async_client.stream("GET", atsu_url) as response:
                print("INFO: stream opened", response.status_code)
                assert response.status_code == 200
                assert response.headers["content-type"].startswith("text/event-stream")

                found = False
                async for line in response.aiter_lines():
                    print(line)

                    if line.startswith("data:"):
                        found = True
                        assert callsign["callsign"] in line
                        break

                assert found, "No data message received from SSE stream"

            await async_client.aclose()
        finally:
            # Restore original Redis methods
            redis_async_db.xrange = old_xrange
            redis_async_db.xread = old_xread

    def test_invalid_auth(self, client: TestClient):
        """Test an invalid api key"""
        client.headers.update({"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30"})
        response = client.get("/atsu/rx/vatsim/wiffle")
        assert response.status_code == 401
