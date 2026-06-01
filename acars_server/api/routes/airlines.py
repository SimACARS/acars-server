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
from dns.resolver import Resolver

# Third Party Libraries
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select

# Local Libraries
from acars_server import common, databases, static_data
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
    session: databases.SessionDep
    ):
    """Authenticate a new airline and generate an API key"""
    if msg.network in static_data.NETWORKS:

        # Check to see if verified callsign exists for this network already
        db_check = select(databases.AirlineApiKey).where(
            (databases.AirlineApiKey.airline_callsign == msg.airline_callsign),
            (databases.AirlineApiKey.network == msg.network),)
        db_result = session.exec(db_check).first()
        if db_result:
            return JSONResponse(content={
                "error": f"{msg.airline_callsign} already exists and is controlled by {msg.domain}"
                })

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

@router.get("/domain_auth/{verification_token}")
async def domain_auth_check(verification_token:str, session: databases.SessionDep):
    """Checks to see if a verification code has been added to the domain"""
    verifcation_request = databases.AirlineVerification.find(
        (databases.AirlineVerification.verification_token == verification_token)
    ).first()
    if len(verification_token) == 1:
        res = Resolver()
        res.nameservers = ["8.8.8.8", "1.1.1.1"]
        dns_answers = res.resolve(
            f"_acars-verification.{verifcation_request.domain}",
            "TXT"
        )
        for txt in dns_answers:
            if txt == verifcation_request.verification_token:
                new_record = {
                    "api_key": secrets.token_hex(64),
                    "network": verifcation_request.network,
                    "airline_name": verifcation_request.airline_name,
                    "airline_callsign": verifcation_request.airline_callsign,
                    "domain": verifcation_request.domain,
                    "verified": True,
                    "created": dt.now(tz.utc).timestamp()
                }

                # Validate and add record to database
                validated_record = databases.AirlineApiKeyCreate.model_validate(new_record)
                session.add(validated_record)
                session.commit()
                session.refresh(validated_record)

                # Remove record for Airline Verification
                verifcation_request.delete(verifcation_request.pk)

                return JSONResponse(content={"api_key": validated_record.api_key})
