"""
ACARS Server
Logon Service Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from datetime import datetime as dt, timezone as tz
from hashlib import blake2b

# Third Party Libraries
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
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

@router.get("/ls/contact/{callsign}")
async def ls_cm_contact(
    callsign:str,
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

        # Get the primary frequency for the ATSU
        try:
            get_freq = databases.DataLinkInitiationCapability.find(
                    (databases.DataLinkInitiationCapability.logon_from == callsign_chk)
                    & (databases.DataLinkInitiationCapability.logon_to == "_SYSTEM_DLIC")
                    & (databases.DataLinkInitiationCapability.primary_frequency != None)
                ).first()
        except NotFoundError:
            return JSONResponse(
                status_code=404,
                content={
                    "error": f"{callsign_chk} is not active on the network"})

        dtg = dt.now(tz.utc).strftime("%y%m%d%H%M%S")
        msg = {
            "msg_from": callsign_chk,
            "msg_to": callsign,
            "msg_type": "cpdlc",
            "msg_packet": f"1//{dtg}/WU/UM117,{callsign_chk},{get_freq.primary_frequency}",
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
        return sf_msg

@router.post("/ls/logon", deprecated=True)
async def ls_cm_logon():
    """CM Logon - handled by DLIC"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/ls/forward", deprecated=True)
async def ls_cm_forward():
    """Allows an ATSU to forward a logon request from an airspace user"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/ls/user-abort", deprecated=True)
async def ls_cm_user_abort():
    """Allows a user to logoff"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})

@router.post("/ls/provider-abort", deprecated=True)
async def ls_cm_provider_abort():
    """Allows a provider to logoff"""
    return JSONResponse(
        status_code=501, content={"error", "not implemented, use DLIC routes instead"})
