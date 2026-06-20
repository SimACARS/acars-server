"""
ACARS Server
Logon Service Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from redis_om.model.model import NotFoundError
from sqlmodel import select # type: ignore

# Local Libraries
from acars_server import common, databases
from acars_server.api.services.auth_services import (
    callsign_verification,
    jwt_auth
    )

router = APIRouter()

@router.get("/contact/{callsign}")
async def ls_cm_contact(
    callsign:str,
    session: databases.SessionDep,
    jwt:HTTPAuthorizationCredentials = Security(common.header_bearer)):
    """
    Attempts to send a UM117 (CONTACT  [unit  name]  [frequency]) to the provided callsign
    """
    if re.match(r"[A-Z0-9]+", callsign):
        user_data = await jwt_auth.decode_jwt(jwt, ["acars:atsu"])
        callsign_chk = await callsign_verification(user_data)
        if callsign_chk is None:
            return JSONResponse(
                status_code=403,
                content={"detail": "Unauthorised callsign for provided JWT"}
            )

        # Get the 'parent' ATSU callsign
        parent = select(
            databases.ATSUAuthorisedCallsign).where(
                databases.ATSUAuthorisedCallsign.callsign == callsign_chk)
        result = session.exec(parent).first()

        if result:
            # Get the primary frequency for the ATSU
            atsu_cs = result.atsu_callsign.atsu_callsign
            try:
                get_freq = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == atsu_cs)
                    & (databases.DataLinkInitiationCapability.logon_to == "_SYSTEM_DLIC")
                    & (databases.DataLinkInitiationCapability.primary_frequency != "100.000")
                ).first()
            except NotFoundError:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": f"{callsign_chk} is not active on the network"})

            dtg = dt.now(tz.utc).strftime("%y%m%d%H%M%S")
            msg = {
                "msg_from": result.atsu_callsign.atsu_callsign,
                "msg_to": callsign,
                "msg_type": "cpdlc",
                "packet": f"1//{dtg}/WU/UM117,{callsign_chk},{get_freq.primary_frequency}",
                "network": user_data["network"],
                "created": dt.now(tz.utc).timestamp()
            }

            sf_msg = databases.StoreAndForward.model_validate(msg)

            # An ATSU should only be able to send a message to an online station
            try:
                databases.DataLinkInitiationCapability.find(
                        (databases.DataLinkInitiationCapability.logon_from == sf_msg.msg_to)
                    ).first()
            except NotFoundError:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": f"{sf_msg.msg_to} is not active on the network"})

            # Save the message to the store and forward.
            # Expire message in 5 minutes if not retrieved.
            sf_msg.save()
            databases.redis_db.expire(
                    sf_msg.key(),
                    300,
                )
            return JSONResponse(status_code=201, content=sf_msg.model_dump_json())
    return JSONResponse(status_code=404, content={"error": "callsign validation error"})

@router.post("/logon", deprecated=True)
async def ls_cm_logon():
    """CM Logon - handled by DLIC"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/forward", deprecated=True)
async def ls_cm_forward():
    """Allows an ATSU to forward a logon request from an airspace user"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/user-abort", deprecated=True)
async def ls_cm_user_abort():
    """Allows a user to logoff"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/provider-abort", deprecated=True)
async def ls_cm_provider_abort():
    """Allows a provider to logoff"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})
