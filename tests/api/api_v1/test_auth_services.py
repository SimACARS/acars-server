"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import secrets
from datetime import timedelta

# Third Party Libraries
import pytest
import requests
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import StoreAndForward
from acars_server.api.message_types.inforeq import Vatsim
from acars_server.api.services.auth_services import (
    callsign_verification,
    check_banned_callsigns,
    JWTAuth
    )
from tests.factories.messages import MessageFactory

LOGON_DATA = {
    "logon_from": "TEST",
    "logon_to": "_SYSTEM",
    "network": "vatsim",
    "created": 0.0,
    "logoff_code": "",
    "fans_1_a_atn_b1": False,
    "atn_b1": False,
    "fans_1_a": False
}

BANNED_CALLSIGNS = [
    "VATGOV72",
    "AAL77",
    "AAL77A",
    "DR_SUP"
]

AUTHENTICATED_END_POINTS = [
    #("/airline/rx/vatsim/BAW123", "get", None),
    ("/airline/tx/atn_vhf", "post", MessageFactory()),
    ("/acars/poll", "post", None),
    ("/acars/tx/atn_vhf", "post", MessageFactory()),
    ("/dlic/airline/logon", "post", LOGON_DATA),
    ("/dlic/aircraft/logon", "post", LOGON_DATA),
    ("/dlic/aircraft/logoff", "post", {"logoff_code": secrets.token_hex(32)}),
    ("/dlic/airline/logoff", "post", {"logoff_code": secrets.token_hex(32)}),
]

@pytest.mark.parametrize("end_point,method,_data", AUTHENTICATED_END_POINTS)
def test_auth_endpoint_no_api_key(client: TestClient, end_point, method, _data):
    """Tests an auth endpoint with no API key"""
    if method == "get":
        request = client.get(end_point)
    else:
        request = client.post(end_point)

    assert request.status_code == 401, f"{end_point} returned {request.status_code}"

@pytest.mark.parametrize("end_point,method,data", AUTHENTICATED_END_POINTS)
def test_auth_endpoint_false_api_key(client: TestClient, end_point, method, data):
    """Tests an auth endpoint with no API key"""
    message: StoreAndForward = MessageFactory() # type: ignore
    api_key = secrets.token_hex(32)
    print(message)
    client.headers.update({"x-key": api_key})
    if method == "get":
        request = client.get(end_point)
    else:
        if data is not None:
            try:
                request = client.post(end_point, json=data.model_dump())
            except AttributeError:
                request = client.post(end_point, json=data)
        else:
            request = client.post(end_point)
    print(request.json())
    assert request.status_code == 401
    client.headers.pop("x-key")

@pytest.mark.parametrize("callsign", BANNED_CALLSIGNS)
def test_banned_callsign(callsign):
    """Tests banned callsigns"""
    print(callsign)
    with pytest.raises(HTTPException) as err:
        check_banned_callsigns(callsign)

@pytest.mark.asyncio
async def test_get_callsign_from_vatsim_cid():
    """Tests getting a callsign from a CID"""
    v = Vatsim()
    rqt = requests.get(v.vatsim_urls['all'], timeout=10)
    if rqt.status_code != 200:
        pytest.skip(f"Response {rqt.status_code} received from {rqt.url}")

    # Pick a random(ish) CID from live VATSIM data
    cid = rqt.json()["pilots"][0]["cid"]
    callsign = rqt.json()["pilots"][0]["callsign"]

    t_request = await callsign_verification({"network": "vatsim", "uid": cid})

    assert t_request == callsign

@pytest.mark.asyncio
async def test_give_wrong_callsign_from_vatsim_cid():
    """Tests what happens when a CID doesn't correlate to the given callsign"""
    v = Vatsim()
    rqt = requests.get(v.vatsim_urls['all'], timeout=10)
    if rqt.status_code != 200:
        pytest.skip(f"Response {rqt.status_code} received from {rqt.url}")

    # Pick a random(ish) CID from live VATSIM data
    cid = rqt.json()["pilots"][0]["cid"]
    real_callsign = rqt.json()["pilots"][0]["callsign"]
    callsign = "THIS_IS_FAKE"

    t_request = await callsign_verification({"network": "vatsim", "uid": cid})

    assert t_request != callsign
    assert t_request == real_callsign

@pytest.mark.asyncio
async def test_give_invalid_cid_to_vatsim():
    """Tests what happens if an invalid CID is provided"""
    cid = "A"

    t_request = await callsign_verification({"network": "vatsim", "uid": cid})

    assert t_request is None

@pytest.mark.asyncio
async def test_give_invalid_network():
    """Tests what happens when an incorrect network is provided"""
    cid = "000000"

    with pytest.raises(HTTPException):
        await callsign_verification({"network": "wiffle", "uid": cid})


class TestJWTRefresh:
    """Test JWT Refresh"""
    @pytest.mark.asyncio
    async def test_valid_expired_jwt_inside_leeway(self, client:TestClient):
        """Test a valid expired JWT which is inside leeway window"""
        # Generate an expired JWT
        jwt_auth = JWTAuth()
        signed_jwt = await jwt_auth.sign_jwt(
            "vatsim",
            "12345678",
            "d6ZcInCUE9EFxSd3x1Vo2UnfWuXoHT9rO7sZrDicitrPe60KEKNMkDFxntlzq1Ja",
            ["acars:atsu"],
            timedelta(microseconds=0)
        )
        print(signed_jwt)

        # Pass auth headers to endpoint
        client.headers.update({"Authorization": f"Bearer {signed_jwt['access_token']}"})
        response = client.post("/callback/atsu/refresh")
        print(response.content)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_valid_expired_jwt_outside_leeway(self, client:TestClient):
        """Test a valid expired JWT which is inside leeway window"""
        # Generate an expired JWT
        jwt_auth = JWTAuth()
        signed_jwt = await jwt_auth.sign_jwt(
            "vatsim",
            "12345678",
            "d6ZcInCUE9EFxSd3x1Vo2UnfWuXoHT9rO7sZrDicitrPe60KEKNMkDFxntlzq1Ja",
            ["acars:atsu"],
            timedelta(minutes=-10)
        )
        print(signed_jwt)

        # Pass auth headers to endpoint
        client.headers.update({"Authorization": f"Bearer {signed_jwt['access_token']}"})
        response = client.post("/callback/atsu/refresh")
        print(response.content)
        assert response.status_code == 401
        assert response.json()["detail"] == "JWT expired signature"

    @pytest.mark.asyncio
    async def test_valid_expired_jwt_invalid_audience(self, client:TestClient):
        """Test a valid expired JWT which is inside leeway window"""
        # Generate an expired JWT
        jwt_auth = JWTAuth()
        signed_jwt = await jwt_auth.sign_jwt(
            "vatsim",
            "12345678",
            "d6ZcInCUE9EFxSd3x1Vo2UnfWuXoHT9rO7sZrDicitrPe60KEKNMkDFxntlzq1Ja",
            ["acars:none"],
            timedelta(minutes=0)
        )
        print(signed_jwt)

        # Pass auth headers to endpoint
        client.headers.update({"Authorization": f"Bearer {signed_jwt['access_token']}"})
        response = client.post("/callback/atsu/refresh")
        print(response.content)
        assert response.status_code == 401
        assert response.json()["detail"] == "JWT invalid audience"

    @pytest.mark.asyncio
    async def test_valid_expired_jwt_invalid_signature(self, client:TestClient):
        """Test a valid expired JWT which is inside leeway window"""
        # Generate an expired JWT with an invalid signature
        jwt_auth = JWTAuth()
        jwt_auth.JWT_SECRET = "GSzexYbt2zpntRSUrJ6Pdome5NEyFfXsHjl1eqtUDNjHCMCyyPdkwLFVAH7mUUf"
        signed_jwt = await jwt_auth.sign_jwt(
            "vatsim",
            "12345678",
            "d6ZcInCUE9EFxSd3x1Vo2UnfWuXoHT9rO7sZrDicitrPe60KEKNMkDFxntlzq1Ja",
            ["acars:atsu"],
            timedelta(minutes=0)
        )
        print(signed_jwt)

        # Pass auth headers to endpoint
        client.headers.update({"Authorization": f"Bearer {signed_jwt['access_token']}"})
        response = client.post("/callback/atsu/refresh")
        print(response.content)
        assert response.status_code == 401
        assert response.json()["detail"] == "JWT invalid signature"
