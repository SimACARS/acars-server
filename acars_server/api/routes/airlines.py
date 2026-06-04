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
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from redis_om.model.model import NotFoundError
from sqlmodel import select
from sse_starlette.event import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

# Local Libraries
from acars_server import common, databases, static_data, tasks
from acars_server.api.services.auth_services import airline_api_authentication
from acars_server.api.services.user_services import responses_user_new_network

templates = Jinja2Templates(directory=os.path.join(common.PWD, "api", "templates"))
router = APIRouter()
# ------------------------------------------------------------------
# Airline Endpoints
# ------------------------------------------------------------------
@router.get(
        "/rx/{network}/{callsign}",
        tags=["Messaging"]
        )
async def receive_message_stream(
    callsign:str,
    network:str,
    session:databases.SessionDep,
    last_event_id: str | None = Query(default=None),
    api_key:str = Depends(common.header_api_key)
    ):
    """
    Airline receive messages via HTTPX (Server-Sent Events)

    Example client side JavaScript:

        const es = new EventSource("/stream/BAW");

        es.onmessage = (event) => {
            console.log("MSG:", JSON.parse(event.data));
        };

    https://developer.mozilla.org/en-US/docs/Web/API/EventSource
    """
    try:
        airline_data = await airline_api_authentication(session, api_key)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    if f"_COY_{callsign}" != airline_data.airline_callsign or network != airline_data.network:
        return JSONResponse(
            status_code=403,
            content={"detail": f"{callsign} is an unauthorised callsign for provided API key"}
        )

    stream_key = f"msg:coy:{airline_data.network}:{airline_data.airline_callsign}"
    start_id = last_event_id or "0-0"

    async def event_generator():
        last_id = start_id

        if last_id != "0-0":
            history = await databases.redis_async_db.xrange(
                stream_key,
                min=f"({last_id}",
            )
            for msg_id, fields in history:
                yield ServerSentEvent(data=fields, event="message", id=msg_id, retry=5000)

        while True:
            response = await databases.redis_async_db.xread(
                streams={stream_key: last_id},
                count=10,
                block=5000,
            )
            if not response:
                continue

            _, messages = response[0]
            for msg_id, fields in messages:
                last_id = msg_id
                yield ServerSentEvent(data=fields, event="message", id=msg_id, retry=5000)

    return EventSourceResponse(event_generator())

@router.post(
        "/tx",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.StoreAndForward,
        tags=["Messaging"]
        )
async def transmit_a_message(
    msg:databases.StoreAndForward,
    session:databases.SessionDep,
    background_tasks: BackgroundTasks,
    api_key:str = Depends(common.header_api_key)):
    """Airline Send a Message"""

    try:
        await airline_api_authentication(session, api_key)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    sf_msg = databases.StoreAndForward.model_validate(msg)

    # An airline should only be able to send a message to an online station
    try:
        databases.DataLinkInitiationCapability.find(
                (databases.DataLinkInitiationCapability.logon_from == msg.msg_to)
            ).first()
    except NotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"{msg.msg_to} is not active on the network"})

    background_tasks.add_task(tasks.message_parse, sf_msg)
    return sf_msg

@router.post(
        "/new",
        response_model=databases.AirlineApiKeyPublic,
        responses=responses_user_new_network)
async def auth_new_airline(
    request: Request,
    msg:databases.RequestNewAirline,
    session: databases.SessionDep
    ):
    """Authenticate a new airline and generate an API key"""
    # Check to see if verified callsign exists for this network already
    temp_callsign = f"_COY_{msg.airline_callsign}"
    db_check = select(databases.AirlineApiKey).where(
        (databases.AirlineApiKey.airline_callsign == temp_callsign),
        (databases.AirlineApiKey.network == msg.network),)
    db_result = session.exec(db_check).first()
    if db_result:
        return JSONResponse(status_code=403, content={
            "error": f"{msg.airline_callsign} already exists and is controlled by {msg.domain}"
            })

    if msg.domain is not None:
        # Check to see if request is already live
        all_requests = databases.AirlineVerification.find(
                    (databases.AirlineVerification.airline_callsign == msg.airline_callsign) &
                    (databases.AirlineVerification.network == msg.network)
                ).all()
        if len(all_requests) > 0:
            common.logger.info(f"Request already exists for {all_requests[0].model_dump()}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Request already exists",
                    "data": all_requests[0].model_dump()
                    })

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
        pass # pragma: no cover

@router.get("/domain_auth/{verification_token}")
async def domain_auth_check(verification_token:str, session: databases.SessionDep):
    """Checks to see if a verification code has been added to the domain"""
    try:
        verifcation_request = databases.AirlineVerification.find(
            (databases.AirlineVerification.verification_token == verification_token)
        ).first()
    except NotFoundError:
        return JSONResponse(status_code=404, content={"error": "verification token not recognised"})

    res = Resolver()
    res.nameservers = ["8.8.8.8", "1.1.1.1"]
    dns_answers = res.resolve(
        f"_acars-verification.{verifcation_request.domain}",
        "TXT"
    )
    for txt in dns_answers:
        if txt == f"acars-verify-{verifcation_request.verification_token}":
            new_record = {
                "api_key": secrets.token_hex(64),
                "network": verifcation_request.network,
                "airline_name": verifcation_request.airline_name,
                "airline_callsign": f"_COY_{verifcation_request.airline_callsign}",
                "domain": verifcation_request.domain,
                "verified": True,
                "created": dt.now(tz.utc).timestamp(),
                "last_used": dt.now(tz.utc).timestamp()
            }

            # Validate and add record to database
            validated = databases.AirlineApiKeyCreate.model_validate(new_record)
            orm_obj = databases.AirlineApiKey(**validated.model_dump())
            session.add(orm_obj)
            session.commit()
            session.refresh(orm_obj)

            # Remove record for Airline Verification
            verifcation_request.delete(verifcation_request.pk)

            return JSONResponse(content={"api_key": validated.api_key})
    return JSONResponse(status_code=404, content={"error": "no matching TXT record was found"})
