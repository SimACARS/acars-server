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
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from redis_om.model.model import NotFoundError # type: ignore

# Local Libraries
from acars_server import common, databases
from acars_server.api.services.auth_services import (
    airline_api_authentication,
    api_authentication,
    callsign_verification
    )

router = APIRouter()
# ------------------------------------------------------------------
# DLIC (Data Link Initiation and Capability)
# ------------------------------------------------------------------
async def dlic_logoff_hash(msg:databases.DataLinkInitiationCapability) -> str:
    """Generate a logoff code for a DLIC logoff message"""
    # Load the signing key
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
    api_key:str = Depends(common.header_api_key)
):
    """DLIC Airline Logon"""
    airline_data = await airline_api_authentication(session, api_key)

    if airline_data.airline_callsign != msg.logon_from:
        common.logger.error("401: API Key doesn't match stored airline code")
        raise HTTPException(
            status_code=401,
            detail="Unauthorised: API Key doesn't match stored airline code")

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
    api_key:str = Depends(common.header_api_key)
    ):
    """DLIC Aircraft Logon"""
    user_data = await api_authentication(session, api_key)
    callsign = str(await callsign_verification(user_data))

    cs_logon = None
    try:
        cs_logon = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == callsign)
                ).first()
    except NotFoundError:
        pass

    if cs_logon:
        common.logger.warning(f"{callsign} is already logged on {cs_logon.model_dump()}")
        return JSONResponse(content={
            "status": "already logged on",
            "callsign": callsign,
            "atsu": cs_logon.logon_to
            })

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
    return JSONResponse(content={"status": "logged on", "data": sf2_msg.model_dump()})

@router.post("/{station_type}/logoff")
async def dlic_any_station_logoff(
    msg: databases.LogoffRequest,
    session:databases.SessionDep,
    station_type: str | None = None,
    api_key:str = Depends(common.header_api_key)
    ):
    """DLIC Any Station Logoff"""
    if station_type == "aircraft" or station_type is None:
        await api_authentication(session, api_key)
    elif station_type == "airline":
        await airline_api_authentication(session, api_key)
    elif station_type == "atsu":
        pass
    else:
        raise HTTPException(
            status_code=404,
            detail="Incorrect station type. Needs to be one of aircraft, airline or atsu")


    databases.LogoffRequest.model_validate(msg)

    try:
        sf2_msg = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logoff_code == msg.logoff_code)
                ).first()
        common.logger.debug(sf2_msg)
    except NotFoundError as err:
        common.logger.error(f"Logoff code {msg.logoff_code} not found")
        raise HTTPException(status_code=404, detail="Logoff code not found") from err

    sf2_msg.delete(sf2_msg.pk)
    common.logger.success(f"Logoff successful for {sf2_msg.logon_from}")
    return JSONResponse(content={"status": "logged off", "callsign": sf2_msg.logon_from})
