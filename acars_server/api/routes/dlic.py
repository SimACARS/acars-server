"""
ACARS Server
DLIC (Data Link Initiation and Capability) Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from hashlib import blake2b

# Third Party Libraries
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from opentelemetry import trace
from redis_om.model.model import NotFoundError # type: ignore

# Local Libraries
from acars_server import auth, common, databases, static_data
from acars_server.api.services.auth_services import (
    airline_api_authentication,
    api_authentication,
    callsign_verification,
    jwt_auth
    )

router = APIRouter()
# ------------------------------------------------------------------
# DLIC (Data Link Initiation and Capability)
# ------------------------------------------------------------------
async def dlic_logoff_hash(msg:databases.DataLinkInitiationCapability) -> str:
    """Generate a logoff code for a DLIC logoff message"""
    # Load the signing key
    current_span = trace.get_current_span()
    current_span.add_event(f"DLIC logoff hash requested: {msg.model_dump()}")
    with open(common.AUTH_KEY, "rb") as key_file:
        signing_key = key_file.read()

    smoosh = (f"{msg['logon_from']}:{msg['logon_to']}:"
              f"{msg['pk']}:{dt.now(tz.utc).timestamp()}").encode()
    h = blake2b(digest_size=32, key=signing_key)
    h.update(smoosh)

    return h.hexdigest()

@router.post("/airline/logon")
async def dlic_airline_logon(
    msg:databases.DataLinkInitiationCapability,
    session:databases.SessionDep,
    api_key:str = Security(common.header_api_key)):
    """DLIC Airline Logon"""
    airline_data = await airline_api_authentication(session, api_key)

    if airline_data.airline_callsign != msg.logon_from:
        common.logger.error("401: API Key doesn't match stored airline code")
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorised: API Key doesn't match stored airline code"})

    cs_logon = None
    try:
        cs_logon = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == f"_COY_{msg.logon_from}")
                ).first()
    except NotFoundError:
        pass

    if cs_logon:
        common.logger.warning(f"{msg.logon_from} is already logged on {cs_logon.model_dump()}")
        return JSONResponse(content={
            "status": "already logged on",
            "callsign": msg.logon_from,
            "atsu": cs_logon.logon_to
            })

    logoff_code = await dlic_logoff_hash(msg)
    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "logon_from": f"_COY_{msg.logon_from}",
        "logon_to": "_SYSTEM_DLIC",
        "network": msg.network,
        "fans_1_a_atn_b1": msg.fans_1_a_atn_b1,
        "atn_b1": msg.atn_b1,
        "fans_1_a": msg.fans_1_a,
        "logoff_code": logoff_code
    }
    logon_msg = databases.DataLinkInitiationCapability.model_validate(t_msg)
    common.logger.success(logon_msg)
    logon_msg.save()
    return JSONResponse(content={"status": "logged on", "data": logon_msg.model_dump()})

@router.post("/aircraft/logon")
async def dlic_aircraft_logon(
    msg:databases.DataLinkInitiationCapability,
    session:databases.SessionDep,
    api_key:str = Security(common.header_api_key)
    ):
    """
    DLIC Aircraft Logon
    Returns a JWT for persistant login
    This does <b>not</b> log a user onto an ATSU, a separate DM99 message must be sent
    """
    user_data = await api_authentication(session, api_key)
    if msg.network != "testing":
        callsign = await callsign_verification(user_data)
    else:
        callsign = msg.logon_from
    # Check to see if user is already logged on
    cs_logon = None
    try:
        cs_logon = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == callsign)
                ).first()
        common.logger.warning(f"{callsign} is already logged on {cs_logon.model_dump()}")
        return JSONResponse(content={
            "status": "already logged on",
            "callsign": callsign,
            "atsu": cs_logon.logon_to
            })
    except NotFoundError:
        pass

    sf_msg = databases.DataLinkInitiationCapability.model_validate(msg)
    logoff_code = await dlic_logoff_hash(sf_msg)
    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "logon_from": callsign,
        "logon_to": sf_msg["logon_to"],
        "network": sf_msg["network"],
        "fans_1_a_atn_b1": sf_msg["fans_1_a_atn_b1"],
        "atn_b1": sf_msg["atn_b1"],
        "fans_1_a": sf_msg["fans_1_a"],
        "logoff_code": logoff_code
    }
    sf2_msg = databases.DataLinkInitiationCapability.model_validate(t_msg)
    common.logger.success(sf2_msg)
    sf2_msg.save()
    jwt_response = await jwt_auth.sign_jwt(
        sf_msg["network"],
        user_data["uid"],
        logoff_code,
        ["acars:aircraft"])
    return JSONResponse(content=jwt_response)

@router.post("/atsu/logon")
async def dlic_atsu_logon(
    msg:databases.DataLinkInitiationCapability):
    """
    ATSU authentication is handled by the relevant network (eg VATSIM)
    """
    if msg.network in static_data.NETWORKS:
        if msg.network == "vatsim":
            v_auth = auth.VatsimAuth(redirect_type="atsu")
            v_url = v_auth.authorise()

            # Add state key to redis
            state_model = {
                "oauth_state": v_url[1]
            }
            state_key = databases.OAuthStateStore.model_validate(state_model)

            # Expire state key in 10 minutes
            state_key.save()
            databases.redis_db.expire(
                state_key.key(),
                600,
            )

            common.logger.success("Client redirected to VATSIM OAuth")
            return RedirectResponse(v_url[0])

        error = f"{msg.network} doesn't appear to exist although it really should..."
        common.logger.error(error)
        return JSONResponse(status_code=400, content={"error": error})

    error = (f"{msg.network} is not a recognised network. Needs to be one of "
             f"{', '.join(static_data.NETWORKS)}")
    common.logger.error(error)
    return JSONResponse(status_code=400, content={"error": error})

@router.post("/airline/logoff")
async def dlic_airline_logoff(
    msg: databases.LogoffRequest,
    session:databases.SessionDep,
    api_key:str = Security(common.header_api_key)
    ):
    """DLIC Airline Logoff"""
    await airline_api_authentication(session, api_key)
    return await dlic_logoff(msg)

@router.post("/aircraft/logoff")
async def dlic_aircraft_logoff(
    jwt:HTTPAuthorizationCredentials = Security(common.header_bearer)
    ):
    """DLIC Aircraft Logoff"""
    user_data = await jwt_auth.decode_jwt(jwt, ["acars:aircraft"])
    msg = databases.LogoffRequest.model_validate({"logoff_code": user_data["loc"]})
    return await dlic_logoff(msg)

@router.post("/atsu/logoff")
async def dlic_atsu_logoff(
    jwt:HTTPAuthorizationCredentials = Security(common.header_bearer)
    ):
    """DLIC Aircraft Logoff"""
    user_data = await jwt_auth.decode_jwt(jwt, ["acars:atsu"])
    msg = databases.LogoffRequest.model_validate({"logoff_code": user_data["loc"]})
    return await dlic_logoff(msg)

async def dlic_logoff(msg: databases.LogoffRequest):
    """Process the logoff request"""
    databases.LogoffRequest.model_validate(msg)
    try:
        sf2_msg = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logoff_code == msg.logoff_code)
                ).first()
        common.logger.debug(sf2_msg)
    except NotFoundError:
        common.logger.error(f"Logoff code {msg.logoff_code} not found")
        return JSONResponse(status_code=404, content={"error": "Logoff code not found"})

    sf2_msg.delete(sf2_msg.pk)
    common.logger.success(f"Logoff successful for {sf2_msg.logon_from}")
    return JSONResponse(content={"status": "logged off", "callsign": sf2_msg.logon_from})
