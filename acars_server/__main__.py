"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader
from loguru import logger

# Local Libraries
from acars_server import __VERSION__, auth, message_types

app = FastAPI(
    title="SimACARS",
    description="This is a simulated ACARS server for flight simulation only.",
    version=__VERSION__,
    contact={
        "name": "@chssn",
    },
)
header_api_key = APIKeyHeader(name="x-key")
crypto = auth.Auth()

@app.get("/")
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return {"server_status": "OK", "server_version": __VERSION__}

@app.get("/user/new/{network}")
async def auth_new_user(network: str):
    """Authenticate a new user and generate an API key"""
    if network == "vatsim":
        v_auth = auth.VatsimAuth()
        v_url = v_auth.authorise()
        return {
            "auth_url": v_url[0],
            "callback": f"http://127.0.0.1:8000/callback/oauth/vatsim/{v_url[1]}/"
            }

@app.get("/callback/oauth/vatsim/{state}/{code}")
async def auth_new_user_callback_vatsim(state:str, code:str):
    """A callback point for VATSIM"""
    # Get the access token from VATSIM
    v_auth = auth.VatsimAuth()
    v_token = v_auth.get_access_token(code)

    # Get the user details using the access token
    v_user = v_auth.get_user_details(v_token["access_token"])

    # Generate the API key using the cid
    v_cid = v_user["data"]["cid"]
    api_key = crypto.api_key_generator(v_cid, "vatsim")

    return {
        "network": "vatsim",
        "cid": v_cid,
        "api_key": api_key
    }

@app.get("/msg/get/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Progress"""
    return {"item_id": item_id, "q": q}

@app.post("/msg/post/oooi")
async def post_msg_progress( msg: message_types.MsgOooi, api_key: str = Depends(header_api_key)):
    """Post a message"""
    if api_key == "1234":
        return {"msg_from": msg.sending_station, "msg_to": msg.receiving_station, "msg": msg.msg_smi}
    header_api_key.make_not_authenticated_error()

@app.post("/msg/legacy")
async def legacy_message(msg: message_types.LegacyMessage, api_key: str = Depends(header_api_key)):
    """Legacy message"""
    if api_key == "1234":
        return msg.msg_from
