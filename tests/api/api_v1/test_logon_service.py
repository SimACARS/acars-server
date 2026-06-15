"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import json
import secrets
from typing import Dict, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

# Third Party Libraries
import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.api.services.atsu_services import complete_vatsim_atsu_logon
from tests.factories.user import CidFactory, OAuthStateFactory
from tests.fixtures.auth import Authentication

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


class TestLSContact:
    """Test ATSU Tx"""
    @pytest.mark.asyncio
    @patch("acars_server.api.services.atsu_services.callsign_verification",
            new_callable=AsyncMock)
    @patch("acars_server.api.routes.logon_service.callsign_verification",
                new_callable=AsyncMock)
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    async def test_ls_contact(
        self,
        mock_vatsim_auth_class,
        mock_callsign_verification2_func,
        mock_callsign_verification_func,
        client: TestClient,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth

        # ATSU Generator
        mock_vatsim_auth.get_user_details.return_value = vatsim_oauth_response
        atsu = Authentication(client, "atsu")
        mock_callsign_verification_func.return_value = atsu.info["callsign"]
        mock_callsign_verification2_func.return_value = atsu.info["callsign"]
        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)

        atsu_auth_headers = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        vdata = HTTPAuthorizationCredentials.model_validate(atsu_auth_headers)

        # Aircraft Generator
        aircraft = Authentication(client, "aircraft")
        aircraft.logon()

        client.headers.update({"Authorization": f"{vdata.scheme} {vdata.credentials}"})
        msg_response = client.get(f"/ls/contact/{aircraft.info['callsign']}")
        print(msg_response.json())
        assert msg_response.status_code == 201

    @pytest.mark.asyncio
    @patch("acars_server.api.services.atsu_services.callsign_verification",
            new_callable=AsyncMock)
    @patch("acars_server.api.routes.logon_service.callsign_verification",
            new_callable=AsyncMock)
    @patch("acars_server.api.routes.callbacks.auth.VatsimAuth")
    async def test_ls_contact_offline(
        self,
        mock_vatsim_auth_class,
        mock_callsign_verification2_func,
        mock_callsign_verification_func,
        client: TestClient,
        db,
        vatsim_oauth_response):
        """Complete VATSIM ATSU Logon"""
        mock_vatsim_auth = MagicMock()
        mock_vatsim_auth_class.return_value = mock_vatsim_auth

        # ATSU Generator
        mock_vatsim_auth.get_user_details.return_value = vatsim_oauth_response
        atsu = Authentication(client, "atsu")
        mock_callsign_verification_func.return_value = atsu.info["callsign"]
        mock_callsign_verification2_func.return_value = atsu.info["callsign"]
        response = await complete_vatsim_atsu_logon(vatsim_oauth_response[1], db)

        atsu_auth_headers = {
            "scheme": "Bearer",
            "credentials": json.loads(response.body)["access_token"]
        }
        vdata = HTTPAuthorizationCredentials.model_validate(atsu_auth_headers)

        # Aircraft Generator
        aircraft = Authentication(client, "aircraft")

        client.headers.update({"Authorization": f"{vdata.scheme} {vdata.credentials}"})
        msg_response = client.get(f"/ls/contact/{aircraft.info['callsign']}")
        print(msg_response.json())
        assert msg_response.status_code == 404
