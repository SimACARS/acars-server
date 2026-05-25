"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from contextlib import asynccontextmanager
from datetime import datetime as dt, timezone as tz
from typing import Annotated

# Third Party Libraries
from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.security import APIKeyHeader
from loguru import logger
from sqlmodel import select

# Local Libraries
from acars_server import __VERSION__, auth, sql, static_data, stations

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
    description=(
        "This is a simulated ACARS network for flight simulation only.<br /><br />"
        "If you are flying on a network, your API key is an encrypted string of SECRET:NETWORK:USER_ID. "
        "Your network user ID is used to verify that the callsign you have logged on with.<br /><br />"
        "Your user ID is verified using your network's OAuth2 protocol. We ONLY store your encrypted user ID and no other personal data."),
    version=__VERSION__,
    contact={
        "name": "@chssn",
    },
    openapi_tags=static_data.METADATA_TAGS
)
header_api_key = APIKeyHeader(name="x-key")
crypto = auth.Auth()

# ------------------------------------------------------------------
# Server Status
# ------------------------------------------------------------------
@app.get("/", tags=["status"])
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return {"server_status": "OK", "server_version": __VERSION__}

# ------------------------------------------------------------------
# User Functions
# ------------------------------------------------------------------
@app.get("/user/new/{network}", tags=["user management"])
async def auth_new_user(network: str):
    """Authenticate a new user and generate an API key"""
    if network == "vatsim":
        v_auth = auth.VatsimAuth()
        v_url = v_auth.authorise()
        return {
            "auth_url": v_url[0],
            "callback": f"http://127.0.0.1:8000/callback/oauth/vatsim/{v_url[1]}/"
            }

@app.get(
        "/callback/oauth/vatsim/{state}/{code}",
        response_model=sql.ApiKeyPublic,
        tags=["callbacks"])
async def auth_new_user_callback_vatsim(
    state:str,
    code:str,
    session: sql.SessionDep):
    """A callback point for VATSIM"""
    # Get the access token from VATSIM
    v_auth = auth.VatsimAuth()
    v_token = v_auth.get_access_token(code)
    if v_token[0] != 200:
        raise HTTPException(status_code=v_token[0], detail=v_token[1]["hint"])

    # Get the user details using the access token
    v_user = v_auth.get_user_details(v_token[1]["access_token"])
    if v_user[0] != 200:
        raise HTTPException(status_code=v_user[0], detail=v_user[1])

    # Generate the API key using the cid
    v_cid = v_user[1]["data"]["cid"]
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

@app.get("/test/update_lut", responses=static_data.COMMON_ERRORS)
async def test_update_lut(session: sql.SessionDep):
    db_select = select(sql.ApiKey).where(sql.ApiKey.api_key == "12345")
    api_user = session.exec(db_select).first()
    if not api_user:
        raise HTTPException(status_code=401, detail="Unauthorised")
    else:
        # Update last used time
        api_lut = {
            "last_used": dt.now(tz.utc).timestamp()
        }
        api_update = sql.ApiKeyUpdate.model_validate(api_lut)
        api_data = api_update.model_dump(exclude_unset=True)
        api_user.sqlmodel_update(api_data)
        session.add(api_user)
        session.commit()
        session.refresh(api_user)
        return "ok"

# ------------------------------------------------------------------
# ACARS Functions
# ------------------------------------------------------------------
@app.get("/msg/get/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Progress"""
    return {"item_id": item_id, "q": q}

@app.post("/msg/post/oooi", status_code=201, responses=static_data.COMMON_ERRORS)
async def post_msg_progress(
    msg:str,
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)):
    """Post a message"""
    # ------------------------------------------------------------------
    # API Auth
    # ------------------------------------------------------------------
    db_select = select(sql.ApiKey).where(sql.ApiKey.api_key == api_key)
    api_user = session.exec(db_select).first()
    if not api_user:
        raise HTTPException(status_code=401, detail="Unauthorised")
    else:
        # ------------------------------------------------------------------
        # Function
        # ------------------------------------------------------------------
        pass

@app.get("/connect.html", tags=["legacy messaging"])
async def hoppie_formated_url(
    api_key: Annotated[str, Query(alias="logon")],
    msg_from: Annotated[str, Query(alias="from")],
    msg_to: Annotated[str, Query(alias="to")],
    msg_type: Annotated[str, Query(alias="type")],
    packet: Annotated[str, Query(alias="packet")],
    session:sql.SessionDep,
    ):
    """
    Provides a psudo html endpoint for legacy clients.
    Connects directly to the <b>/msg/legacy/tx</b> endpoint
    """
    msg = {
        "msg_from": msg_from,
        "msg_to": msg_to,
        "msg_type": msg_type,
        "packet": packet
    }
    sf_msg = sql.StoreAndForwardCreate.model_validate(msg)
    await legacy_messaging(msg=sf_msg, api_key=api_key, session=session)

@app.post(
        "/msg/legacy/tx",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=sql.StoreAndForwardPublic,
        tags=["legacy messaging"]
        )
async def legacy_messaging(
    msg:sql.StoreAndForwardCreate,
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)):
    """Legacy message"""
    # ------------------------------------------------------------------
    # API Auth
    # ------------------------------------------------------------------
    db_select = select(sql.ApiKey).where(sql.ApiKey.api_key == api_key)
    api_user = session.exec(db_select).first()
    if not api_user:
        raise HTTPException(status_code=401, detail="Unauthorised")
    else:
        # ------------------------------------------------------------------
        # Function
        # ------------------------------------------------------------------

        # Read API Key
        user_data = crypto.api_key_reader(api_key)
        sf_msg = sql.StoreAndForward.model_validate(msg)

        # Validate callsign on various networks
        check = False
        if user_data["network"] == "vatsim":
            vc = stations.Vatsim()
            check = vc.corrolate_cid_to_callsign(user_data["uid"], sf_msg["msg_from"])
        elif user_data["network"] == "ivao":
            pass
        else:
            raise HTTPException(status_code=400, detail=f"Network '{user_data['network']}' is not valid. Expected one of {', '.join(static_data.NETWORKS)}")

        # If the callsign has been validated
        if check:
            session.add(sf_msg)
            session.commit()
            session.refresh(sf_msg)
            return sf_msg
        raise HTTPException(status_code=403, detail=f"Callsign validation failed - Network: {user_data['network']}, User ID: {user_data['uid']}, Callsign: {sf_msg['msg_from']}")
