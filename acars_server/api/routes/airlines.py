"""
ACARS Server
Airline Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import secrets
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# Local Libraries
from acars_server import auth, common, databases, static_data
from acars_server.api.services.user_services import responses_user_new_network

templates = Jinja2Templates(directory=os.path.join(common.PWD, "api", "templates"))
router = APIRouter()
# ------------------------------------------------------------------
# Airline Endpoints
# ------------------------------------------------------------------
@router.post(
        "/new",
        response_model=databases.AirlineApiKeyPublic,
        responses=responses_user_new_network)
async def auth_new_airline(
    request: Request,
    msg:databases.AirlineApiKeyCreate,
    ):
    """Authenticate a new airline and generate an API key"""
    if msg.network in static_data.NETWORKS:
        if msg.domain is not None:
            # Check to see if request is already live
            all_requests = databases.AirlineVerification.find(
                            (databases.AirlineVerification.airline_callsign == msg.airline_callsign) &
                            (databases.AirlineVerification.network == msg.network) &
                            (databases.AirlineVerification.airline_name == msg.airline_name)
                        ).all()
            if len(all_requests) > 0:
                common.logger.info(f"Request already exists for {all_requests[0].model_dump()}")
                return JSONResponse(all_requests[0].model_dump())
            # Generate a random verification token
            verification_token = secrets.token_urlsafe(32)

            # Store the verification token in Redis with a TTL of 24 hours
            verification = databases.AirlineVerification(
                verification_token=verification_token,
                network=msg.network,
                airline_name=msg.airline_name,
                airline_callsign=msg.airline_callsign,
                domain=msg.domain,
            )
            verification.save()
            databases.redis_db.expire(
                verification.key(),
                86400,
            )
            return templates.TemplateResponse(
                request=request,
                name="airline_domain_verification.html",
                context={"verification_token": verification_token, "domain": msg.domain}
                )
        else:
            # If no domain provided, just generate temporary API key and return it
            pass

    error = (f"{msg.network} is not a recognised network. Needs to be one of "
             f"{', '.join(static_data.NETWORKS)}")
    common.logger.error(error)
    raise HTTPException(
        status_code=400,
        detail=error)


"""all_messages = databases.DataLinkInitiationCapability.find(
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
    sf2_msg.save()"""