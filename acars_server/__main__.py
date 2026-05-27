"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from contextlib import asynccontextmanager
from datetime import datetime as dt, timezone as tz
from pathlib import Path
from time import sleep
from typing import Annotated, Any, Dict, List

# Third Party Libraries
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import APIKeyHeader
from fastapi.staticfiles import StaticFiles
from sqlmodel import and_, select, update
from sse_starlette.sse import EventSourceResponse

# Local Libraries
from acars_server import __VERSION__, auth, common, sql, static_data, networks, tasks

PWD = Path(os.path.dirname(__file__))
MASTER_KEY = os.path.join(PWD.parent, "master.key")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """async Context Manager"""
    # ------------------------------------------------------------------
    # Pre App Start
    # ------------------------------------------------------------------

    # Create DB and Tables
    sql.create_db_and_tables()

    # ------------------------------------------------------------------
    # App Start
    # ------------------------------------------------------------------
    yield

    # ------------------------------------------------------------------
    # Post App Finish
    # ------------------------------------------------------------------

app = FastAPI(
    lifespan=lifespan,
    title="SimACARS",
    description=(
        "This is a simulated ACARS network for flight simulation only.<br /><br />"
        "If you are flying on a network, your API key is an encrypted string of "
        "SECRET:NETWORK:USER_ID. Your network user ID is used to verify that the "
        "callsign you have logged on with.<br /><br />Your user ID is verified "
        "using your network's OAuth2 protocol. We ONLY store your encrypted user "
        "ID and no other personal data."),
    version=__VERSION__,
    contact={
        "name": "@chssn",
    },
    openapi_tags=static_data.METADATA_TAGS
)
# Serve some static files
app.mount("/static", StaticFiles(directory=os.path.join(PWD.parent, "front_end")), name="static")
# Add the API Key header
header_api_key = APIKeyHeader(name="x-key")

# Check that a master key exists, if not then create one
if not Path(MASTER_KEY).exists():
    auth.generate_key()
    sleep(1)
crypto = auth.Auth()

# ------------------------------------------------------------------
# Server Status
# ------------------------------------------------------------------
@app.get("/", tags=["status"])
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return {"server_status": "OK", "server_version": __VERSION__}

@app.get("/logs/stream")
async def stream_logs():
    """Log Streamer"""
    async def event_generator():
        while True:
            # Get item from the queue
            item = await common.stream.get()

            yield {
                "event": "log",
                "data": item
            }

            # Compete the processing
            common.stream.task_done()

    return EventSourceResponse(event_generator())

# ------------------------------------------------------------------
# User Functions
# ------------------------------------------------------------------
responses_user_new_network:dict[int|str,dict[str,Any]]|None  = {
    307: {},
    400: {},
    501: {},
}
@app.get("/user/new/{network}", tags=["user management"], responses=responses_user_new_network)
async def auth_new_user(network: str):
    """Authenticate a new user and generate an API key"""
    if network in static_data.NETWORKS:
        if network == "vatsim":
            v_auth = auth.VatsimAuth()
            v_url = v_auth.authorise()
            return RedirectResponse(v_url[0])
        raise HTTPException(
            status_code=501,
            detail=f"{network} doesn't appear to exist although it really should...")
    raise HTTPException(
        status_code=400,
        detail=(f"{network} is not a recognised network. Needs to be one of "
                f"{', '.join(static_data.NETWORKS)}"))

@app.get(
        "/callback/oauth/vatsim/{state}/{code}",
        response_model=sql.ApiKeyPublic,
        tags=["callbacks"])
async def auth_new_user_callback_vatsim(
    state:str,
    code:str,
    session: sql.SessionDep
    ):
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
@app.get("/test/poll/{callsign}", tags=["testing"])
async def test_poll(callsign:str, session: sql.SessionDep) -> Response:
    """Test POLL"""
    # If the callsign has been validated
    update_msg = {
        "relayed": True,
        "relayed_at": dt.now(tz.utc).timestamp()
    }
    db_select = select(sql.StoreAndForward).where(and_(
        sql.StoreAndForward.msg_to == callsign, sql.StoreAndForward.relayed.is_(None)))
    all_messages = session.exec(db_select).fetchall()
    if len(all_messages) > 0:
        rtn:Dict[str, Any] = {"message_count": len(all_messages), "messages": []}
        update_id_list = []
        for m in all_messages:
            update_id_list.append(m["id"])
            data_block = {
                "id": m["id"],
                "msg_from": m["msg_from"],
                "msg_to": m["msg_to"],
                "msg_type": m["msg_type"],
                "packet": m["packet"],
                "network": m["network"]
            }
            rtn["messages"].append(data_block)

        if len(update_id_list) > 0:
            stmt = (
                update(sql.StoreAndForward)
                .where(and_(
                    sql.StoreAndForward.msg_to == callsign,
                    sql.StoreAndForward.id.in_(update_id_list)))
                .values(**update_msg)
                )

            session.exec(stmt)
            session.commit()
        common.logger.success(f"Messages retrieved {rtn}")
        return JSONResponse(rtn)
    common.logger.success("No messages to retrive")
    return JSONResponse(content={"msg_count": 0})

@app.get("/test/{ir_type}/{network}/{station}", status_code=204, tags=["testing"])
async def test_inforeq(
    ir_type:str,
    network:str,
    station:str,
    background_tasks: BackgroundTasks,
    session: sql.SessionDep
    ):
    """INFOREQ Test"""
    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "msg_type": "inforeq",
        "network": network,
        "packet": ir_type.upper(),
        "msg_to": station,
        "msg_from": "TEST1"
    }
    sf_msg = sql.StoreAndForward.model_validate(t_msg)
    common.logger.success(sf_msg)
    background_tasks.add_task(tasks.message_parse, sf_msg, session)

# ------------------------------------------------------------------
# ACARS Functions
# ------------------------------------------------------------------
@app.post("/msg/poll", responses=static_data.COMMON_ERRORS, tags=["messaging"])
async def poll_for_new_messages(
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)
    ) -> Response:
    """Poll for new messages"""
    # ------------------------------------------------------------------
    # API Auth
    # ------------------------------------------------------------------
    db_auth = select(sql.ApiKey).where(sql.ApiKey.api_key == api_key)
    api_user = session.exec(db_auth).first()
    if not api_user:
        common.logger.error("401: API key not recognised")
        raise HTTPException(status_code=401, detail="Unauthorised")
    # ------------------------------------------------------------------
    # Function
    # ------------------------------------------------------------------

    # Read API Key
    user_data = crypto.api_key_reader(api_key)

    # Validate callsign on various networks
    callsign = None
    if user_data["network"] == "vatsim":
        vc = networks.Vatsim()
        callsign = vc.get_callsign_from_cid(user_data["uid"])
    elif user_data["network"] == "ivao":
        pass
    else:
        common.logger.error(f"400: Network '{user_data['network']}' is not valid. "
                    f"Expected one of {', '.join(static_data.NETWORKS)}")
        raise HTTPException(
            status_code=400,
            detail=(f"Network '{user_data['network']}' is not valid. "
                    f"Expected one of {', '.join(static_data.NETWORKS)}"))

    # If the callsign has been validated
    if callsign:
        update_msg = {
            "relayed": True,
            "relayed_at": dt.now(tz.utc).timestamp()
        }
        db_select = select(sql.StoreAndForward).where(and_(
            sql.StoreAndForward.msg_to == callsign,
            sql.StoreAndForward.relayed.is_(None)))
        all_messages = session.exec(db_select).fetchall()

        if len(all_messages) > 0:
            rtn:Dict[str, Any] = {"message_count": len(all_messages), "messages": []}
            update_id_list:List[str] = []
            for m in all_messages:
                update_id_list.append(m["id"])
                data_block = {
                    "id": m["id"],
                    "msg_from": m["msg_from"],
                    "msg_to": m["msg_to"],
                    "msg_type": m["msg_type"],
                    "packet": m["packet"],
                    "network": m["network"]
                }
                rtn["messages"].append(data_block)

            if len(update_id_list) > 0:
                stmt = (
                    update(sql.StoreAndForward)
                    .where(and_(
                        sql.StoreAndForward.msg_to == callsign,
                        sql.StoreAndForward.id.in_(update_id_list)))
                    .values(**update_msg)
                    )
                session.exec(stmt)
                session.commit()

            return JSONResponse(rtn)
        return JSONResponse(content={"msg_count": 0})
    error = ("Unable to retrieve callsign for user - Network: "
                f"{user_data['network']}, User ID: {user_data['uid']}")
    common.logger.error(error)
    raise HTTPException(
        status_code=403,
        detail=error)

@app.post("/msg/post/oooi", status_code=201, responses=static_data.COMMON_ERRORS)
async def post_msg_progress(
    session:sql.SessionDep,
    api_key:str = Depends(header_api_key)
    ):
    """Post a message"""
    # ------------------------------------------------------------------
    # API Auth
    # ------------------------------------------------------------------
    db_select = select(sql.ApiKey).where(sql.ApiKey.api_key == api_key)
    api_user = session.exec(db_select).first()
    if not api_user:
        raise HTTPException(status_code=401, detail="Unauthorised")
    # ------------------------------------------------------------------
    # Function
    # ------------------------------------------------------------------
    pass

@app.get("/connect.html", tags=["legacy messaging"], deprecated=True)
async def hoppie_formated_url(
    api_key: Annotated[str, Query(alias="logon")],
    msg_from: Annotated[str, Query(alias="from")],
    msg_to: Annotated[str, Query(alias="to")],
    msg_type: Annotated[str, Query(alias="type")],
    packet: Annotated[str, Query(alias="packet")],
    background_tasks: BackgroundTasks,
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
    await transmit_a_message(
        msg=sf_msg,
        api_key=api_key,
        background_tasks=background_tasks,
        session=session)

@app.post(
        "/msg/tx",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=sql.StoreAndForwardPublic,
        tags=["messaging"]
        )
async def transmit_a_message(
    msg:sql.StoreAndForwardCreate,
    session:sql.SessionDep,
    background_tasks: BackgroundTasks,
    api_key:str = Depends(header_api_key)):
    """Legacy message"""
    # ------------------------------------------------------------------
    # API Auth
    # ------------------------------------------------------------------
    db_select = select(sql.ApiKey).where(sql.ApiKey.api_key == api_key)
    api_user = session.exec(db_select).first()
    if not api_user:
        raise HTTPException(status_code=401, detail="Unauthorised")
    # ------------------------------------------------------------------
    # Function
    # ------------------------------------------------------------------

    # Read API Key
    user_data = crypto.api_key_reader(api_key)
    sf_msg = sql.StoreAndForward.model_validate(msg)

    # Validate callsign on various networks
    check = False
    if user_data["network"] == "vatsim":
        vc = networks.Vatsim()
        check = vc.corrolate_cid_to_callsign(user_data["uid"], sf_msg["msg_from"])
    elif user_data["network"] == "ivao":
        pass
    else:
        error = (f"Network '{user_data['network']}' is not valid. "
                f"Expected one of {', '.join(static_data.NETWORKS)}")
        common.logger.error(error)
        raise HTTPException(
            status_code=400,
            detail=error
            )

    # If the callsign has been validated
    if check:
        background_tasks.add_task(tasks.message_parse, sf_msg, session)
        return sf_msg

    error = (f"Callsign validation failed - Network: {user_data['network']}, "
             f"User ID: {user_data['uid']}, Callsign: {sf_msg['msg_from']}")
    common.logger.error(error)
    raise HTTPException(
        status_code=403,
        detail=error
        )
