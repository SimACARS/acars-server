"""
ACARS Server
ATSU Service Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timedelta, timezone as tz
from typing import Any, Dict

# Third Party Libraries
from fastapi.responses import JSONResponse
from redis_om.model.model import NotFoundError # type: ignore
from sqlmodel import select

# Local Libraries
from acars_server import common, databases
from acars_server.api.routes.dlic import dlic_logoff_hash
from acars_server.api.services.auth_services import (
    callsign_verification,
    jwt_auth
    )

async def complete_vatsim_atsu_logon(
        user_data:Dict[str,Any],
        session: databases.SessionDep) -> JSONResponse:
    """
    DLIC ATSU Logon
    Returns a short expiry JWT for persistant login
    """
    # Does the user hold an ATC rating?
    if int(user_data["vatsim"]["rating"]["id"]) <= 1:
        return JSONResponse(status_code=403, content={"error": "No ATC rating found"})

    cvd = {
        "network": "vatsim",
        "uid": user_data["cid"]
    }
    # What callsign is the user logged on as?
    callsign = await callsign_verification(cvd)

    # Determine the appropriate ATSU logon based on Division staff information
    db_check = select(databases.ATSUAuthorisedCallsign).where(
            (databases.ATSUAuthorisedCallsign.callsign == callsign))
    db_result = session.exec(db_check).first()
    if db_result:
        atsu_callsign = db_result.atsu_callsign
    else:
        return JSONResponse(
            status_code=404,
            content={
                "error": f"{callsign} is not linked to an ATSU callsign",
                })

    cs_logon = None
    try:
        cs_logon = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == atsu_callsign)
                ).first()
    except NotFoundError:
        pass

    if cs_logon:
        common.logger.warning(f"{atsu_callsign} is already logged on {cs_logon.model_dump()}")
        return JSONResponse(content={
            "status": "already logged on",
            "callsign": atsu_callsign,
            "atsu": cs_logon.logon_to
            })

    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "logon_from": atsu_callsign,
        "logon_to": "_SYSTEM_DLIC",
        "network": "vatsim",
        "fans_1_a_atn_b1": True,
        "atn_b1": True,
        "fans_1_a": True,
        "logoff_code": ""
    }
    loc_v = databases.DataLinkInitiationCapability.model_validate(t_msg)
    logoff_code = await dlic_logoff_hash(loc_v)

    t_msg["logoff_code"] = logoff_code
    sf2_msg = databases.DataLinkInitiationCapability.model_validate(t_msg)
    common.logger.success(sf2_msg)
    sf2_msg.save()
    jwt_response = await jwt_auth.sign_jwt(
        "vatsim",
        user_data["cid"],
        logoff_code,
        ["acars:atsu"],
        timedelta(minutes=10))
    return JSONResponse(content=jwt_response)
