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
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse, parse_qs

# Third Party Libraries
import pytest
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# Local Libraries
from acars_server import databases
from acars_server.api.services.atsu_services import complete_vatsim_atsu_logon
from acars_server.api.services.auth_services import jwt_auth
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

@pytest.fixture
def vatsim_oauth_response():
    """VATSIM OAuth Response"""
    cid = CidFactory()
    return {
        "data": {
            "cid": cid["cid"],
            "vatsim": {
                "rating": {
                    "id": 4
                }
            }
        }
    }


class TestATSULogon:
    """ATSU Logon"""
    def test_atsu_logon(self, client: TestClient):
        """Test to add a new user"""
        atsu_data: databases.ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()
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


class TestATSUCallback:
    """ATSU Callbacks"""
    @patch("acars_server.api.routes.callbacks.complete_vatsim_atsu_logon")
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    def test_callback(self,
        mock_vatsim_auth_class,
        mock_atsu_logon_func,
        client: TestClient
        ):
        """Test the callback with a login attempt"""
        cid = CidFactory()
        mock_atsu_logon = MagicMock()
        mock_vatsim_auth = MagicMock()

        mock_vatsim_auth_class.return_value = mock_vatsim_auth
        mock_atsu_logon_func.return_value = mock_atsu_logon
        state = OAuthStateFactory()

        # ---- mock get_access_token ----
        mock_vatsim_auth.get_access_token.return_value = (
            200,
            {
                "access_token": secrets.token_hex(32),
                "state": state.oauth_state
            }
        )

        # ---- mock get_user_details ----
        mock_vatsim_auth.get_user_details.return_value = (
            200,
            {
                "data": {
                    "cid": cid["cid"],
                    "vatsim": {
                        "rating": {
                            "id": 4
                        }
                    }
                }
            }
        )

        # ---- mock get_access_token ----
        mock_atsu_logon.return_value = JSONResponse(
            status_code=200,
            content={"success": True},
        )

        response = client.get(
            f"/callback/oauth/vatsim/atsu/{state.oauth_state}/{secrets.token_hex(32)}")
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

        # ---- mock get_access_token ----
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

        state = OAuthStateFactory()

        # ---- mock get_access_token ----
        mock_vatsim_auth.get_access_token.return_value = (
            200,
            {"access_token": secrets.token_hex(32)}
        )

        # ---- mock get_user_details ----
        mock_vatsim_auth.get_user_details.return_value = (
            400,
            {"hint": "some hint from the oauth provider"}
        )

        response = client.get(
            f"/callback/oauth/vatsim/atsu/{state.oauth_state}/{secrets.token_hex(32)}")
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
        client: TestClient
        ):
        """Tests a callback with duplicate state code"""
        cid = CidFactory()
        mock_atsu_logon = MagicMock()
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth
        mock_atsu_logon_func.return_value = mock_atsu_logon

        state = OAuthStateFactory()

        # ---- mock get_access_token ----
        mock_vatsim_auth.get_access_token.return_value = (
            200,
            {
                "access_token": secrets.token_hex(32),
                "state": state.oauth_state
            }
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

        # ---- mock get_access_token ----
        mock_atsu_logon.return_value = JSONResponse(
            status_code=200,
            content={"success": True},
        )

        response_a = client.get(
            f"/callback/oauth/vatsim/atsu/{state.oauth_state}/{secrets.token_hex(32)}")

        assert response_a.status_code == 200

        response_b = client.get(
            f"/callback/oauth/vatsim/atsu/{state.oauth_state}/{secrets.token_hex(32)}")

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

        atsu_data: databases.ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()

        mock_callsign_verification_func.return_value = atsu_data.callsign

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response, db)
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
        vor["data"]["vatsim"]["rating"]["id"] = 1

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response, db)

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

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response, db)

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

        atsu_data: databases.ATSUAuthorisedCallsign = ATSUAuthorisedCallsignFactory()

        mock_callsign_verification_func.return_value = atsu_data.callsign

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response, db)
        rdata = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        vdata = HTTPAuthorizationCredentials.model_validate(rdata)

        assert await jwt_auth.decode_jwt(vdata, ["acars:atsu"])

        response = await complete_vatsim_atsu_logon(vatsim_oauth_response, db)
        data = json.loads(response.body)
        assert response.status_code == 200
        assert data["status"] == "already logged on"
