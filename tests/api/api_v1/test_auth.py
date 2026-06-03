"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import requests
import secrets

# Third Party Libraries
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import StoreAndForward
from acars_server.api.message_types.inforeq import Vatsim
from acars_server.api.services.auth_services import callsign_verification
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

AUTHENTICATED_END_POINTS = [
    ("/airline/rx/vatsim/BAW123", "get", None),
    ("/airline/tx", "post", MessageFactory()),
    ("/acars/poll", "post", None),
    ("/acars/tx", "post", MessageFactory()),
    ("/dlic/airline/logon", "post", LOGON_DATA),
    ("/dlic/aircraft/logon", "post", LOGON_DATA),
    ("/dlic/aircraft/logoff", "post", {"logoff_code": secrets.token_hex(32)}),
    ("/dlic/airline/logoff", "post", {"logoff_code": secrets.token_hex(32)}),
]
def test_auth_endpoint_no_api_key(client: TestClient):
    """Tests an auth endpoint with no API key"""
    for end_point, method, _ in AUTHENTICATED_END_POINTS:
        if method == "get":
            request = client.get(end_point)
        else:
            request = client.post(end_point)

        assert request.status_code == 401, f"{end_point} returned {request.status_code}"

def test_auth_endpoint_false_api_key(client: TestClient):
    """Tests an auth endpoint with no API key"""
    message: StoreAndForward = MessageFactory()
    api_key = secrets.token_hex(32)
    print(message)
    client.headers.update({"x-key": api_key})
    for end_point, method, data in AUTHENTICATED_END_POINTS:
        print(end_point)
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

@pytest.mark.asyncio
async def test_get_callsign_from_vatsim_cid():
    """Tests getting a callsign from a CID"""
    v = Vatsim()
    rqt = requests.get(v.vatsim_urls['all'], timeout=10)
    assert rqt.status_code == 200

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
    assert rqt.status_code == 200

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
