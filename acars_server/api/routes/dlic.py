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
from acars_server.api.services.auth_services import api_authentication, callsign_verification

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
              "{msg['pk']}:{dt.now(tz.utc).timestamp()}").encode()
    h = blake2b(digest_size=32, key=signing_key)
    h.update(smoosh)

    return h.hexdigest()

@router.post("/aircraft/logon")
async def dlic_aircraft_logon(
    msg:databases.DataLinkInitiationCapability,
    session:databases.SessionDep,
    api_key:str = Depends(common.header_api_key)
    ):
    """DLIC Aircraft Logon"""
    user_data = await api_authentication(session, api_key)
    if msg.network == "testing":
        common.logger.warning(
            ("Message received with network 'testing' - This is only for testing "
             "purposes and should not be used in production"))
        callsign = str(msg.logon_from)
    else:
        callsign = await callsign_verification(user_data)

    all_messages = databases.DataLinkInitiationCapability.find(
                (databases.DataLinkInitiationCapability.logon_from == callsign)
            ).all()
    if len(all_messages) > 0:
        common.logger.warning(f"{callsign} is already logged on {all_messages[0].model_dump()}")
        return JSONResponse(content={
            "status": "already logged on",
            "callsign": callsign,
            "atsu": all_messages[0].logon_to
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

@router.post("/aircraft/logoff")
async def dlic_aircraft_logoff(
    msg: databases.LogoffRequest,
    session:databases.SessionDep,
    api_key:str = Depends(common.header_api_key)
    ):
    """DLIC Aircraft Logoff"""
    await api_authentication(session, api_key)

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
