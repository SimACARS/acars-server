"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from contextlib import asynccontextmanager
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
from fastapi import Depends, FastAPI
from fastapi.security import APIKeyHeader
from loguru import logger

# Local Libraries
from acars_server import __VERSION__, auth, message_types, sql, static_data

@logger.catch
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB and Tables
    sql.create_db_and_tables()
    # Run the app
    yield
    # On shutdown cleanup

app = FastAPI(
    lifespan=lifespan,
    title="SimACARS",
    description="This is a simulated ACARS server for flight simulation only.",
    version=__VERSION__,
    contact={
        "name": "@chssn",
    },
)
header_api_key = APIKeyHeader(name="x-key")
crypto = auth.Auth()

# ------------------------------------------------------------------
# Server Status
# ------------------------------------------------------------------
@app.get("/")
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return {"server_status": "OK", "server_version": __VERSION__}

# ------------------------------------------------------------------
# User Functions
# ------------------------------------------------------------------
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

@app.get("/callback/oauth/vatsim/{state}/{code}", response_model=sql.ApiKeyPublic)
async def auth_new_user_callback_vatsim(
    state:str,
    code:str,
    session: sql.SessionDep):
    """A callback point for VATSIM"""
    # Get the access token from VATSIM
    v_auth = auth.VatsimAuth()
    v_token = v_auth.get_access_token(code)

    # Get the user details using the access token
    v_user = v_auth.get_user_details(v_token["access_token"])

    # Generate the API key using the cid
    v_cid = v_user["data"]["cid"]
    api_key = crypto.api_key_generator(v_cid, "vatsim")

    # Add the API key to the DB
    dtnow = dt.now(tz.utc).timestamp()
    db_data = {
        "api_key": api_key,
        "network": "vatsim",
        "created": dtnow,
        "last_used": dtnow
    }
    db_add = sql.ApiKey.model_validate(db_data)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return db_add

# ------------------------------------------------------------------
# Test Functions
# ------------------------------------------------------------------
@app.post("/test/newapi", response_model=sql.ApiKeyPublic)
async def test_newapi(session: sql.SessionDep):
    # Add the API key to the DB
    dtnow = dt.now(tz.utc).timestamp()
    db_data = {
        "api_key": "12345",
        "network": "vatsim",
        "created": dtnow,
        "last_used": dtnow
    }
    db_add = sql.ApiKey.model_validate(db_data)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return db_add

# ------------------------------------------------------------------
# ACARS Functions
# ------------------------------------------------------------------
@app.get("/msg/get/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Progress"""
    return {"item_id": item_id, "q": q}

@app.post("/msg/post/oooi", status_code=201, responses=static_data.COMMON_ERRORS)
async def post_msg_progress(
    msg:message_types.MsgOooi,
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)):
    """Post a message"""
    # API Auth
    api_user = session.get(sql.ApiKey, api_key)
    if api_user:
        return
    header_api_key.make_not_authenticated_error()

@app.post("/msg/legacy", status_code=201, responses=static_data.COMMON_ERRORS)
async def legacy_message(
    msg:message_types.LegacyMessage,
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)):
    """Legacy message"""
    # API Auth
    api_user = session.get(sql.ApiKey, api_key)
    if api_user:
        return
    header_api_key.make_not_authenticated_error()
