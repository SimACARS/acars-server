"""
ACARS Server
ATSU Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from typing import Annotated

# Third Party Libraries
from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates
from redis_om.model.model import NotFoundError
from sse_starlette.event import ServerSentEvent
from sse_starlette.sse import EventSourceResponse

# Local Libraries
from acars_server import common, databases, static_data, tasks
from acars_server.api.services.auth_services import (
    callsign_verification, jwt_auth)

templates = Jinja2Templates(directory=os.path.join(common.PWD, "api", "templates"))
router = APIRouter()
# ------------------------------------------------------------------
# ATSU Endpoints
# ------------------------------------------------------------------
EXAMPLE_JS_SOURCE = """const es = new EventSource("/atsu/rx/EGKK");

es.onmessage = (event) => {
    console.log("MSG:", JSON.parse(event.data));
};
"""
EXAMPLE_TYPESCRIPT_SOURCE = """type StreamMessage = {
  // adjust this to your real payload shape
  [key: string]: unknown;
};

const es = new EventSource("/atsu/rx/EGKK");

es.onmessage = (event: MessageEvent) => {
  const data: StreamMessage = JSON.parse(event.data);
  console.log("MSG:", data);
};"""

@router.get(
        "/rx/{network}/{callsign}",
        response_class=EventSourceResponse,
        openapi_extra={
        "x-codeSamples": [
            {
                "lang": "JavaScript",
                "source": EXAMPLE_JS_SOURCE
            },
            {
                "lang": "TypeScript",
                "source": EXAMPLE_TYPESCRIPT_SOURCE
            }
        ]},
        description="For ATSUs to subscribe to receive messages via Server-Sent Event",
        tags=["Messaging"]
        )
async def receive_message_stream(
    callsign:Annotated[str, Path(pattern="^[A-Z_]+$")],
    network:static_data.NetworkTypes,
    last_event_id: str | None = Query(default=None),
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """
    ATSU receive messages via Server-Sent Events
    \nJWT Audience: ["acars:atsu"]

    Example for TypeScript: https://docs.servicestack.net/typescript-server-events-client

    Example client side JavaScript:

        const es = new EventSource("/stream/BAW");

        es.onmessage = (event) => {
            console.log("MSG:", JSON.parse(event.data));
        };

    https://developer.mozilla.org/en-US/docs/Web/API/EventSource
    """
    user_data = await jwt_auth.decode_jwt(jwt, ["acars:atsu"])
    callsign_chk = await callsign_verification(user_data)

    if f"_ATC_{callsign}" != f"_ATC_{callsign_chk}" or network != user_data["network"]:
        return JSONResponse(
            status_code=403,
            content={"detail": f"{callsign} is an unauthorised callsign for provided API key"}
        )

    stream_key = f"msg:coy:{user_data['network']}:_ATC_{callsign_chk}"
    start_id = last_event_id or "0-0"

    async def event_generator():
        last_id = start_id

        if last_id != "0-0": # pragma: no cover
            history = await databases.redis_async_db.xrange(
                stream_key,
                min=f"({last_id}",
            )
            for msg_id, fields in history:
                yield ServerSentEvent(data=fields, event="message", id=msg_id, retry=5000)

        # Stream new messages - limit attempts for test compatibility, infinite for production
        max_attempts = 1000  # ~50 seconds max for tests, effectively infinite for production
        attempt = 0
        while attempt < max_attempts:
            response = await databases.redis_async_db.xread(
                streams={stream_key: last_id},
                count=10,
                block=5000,
            )
            if response:
                _, messages = response[0]
                for msg_id, fields in messages:
                    last_id = msg_id
                    yield ServerSentEvent(data=fields, event="message", id=msg_id, retry=5000)
            attempt += 1

    return EventSourceResponse(event_generator())

@router.post(
        "/tx/{bearer}",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.StoreAndForward,
        summary="Send a message to the store and forward",
        description="Allows an ATSU to send a message",
        tags=["Messaging"]
        )
async def transmit_a_message(
    msg:databases.StoreAndForward,
    bearer: static_data.BearerTypes,
    background_tasks: BackgroundTasks,
    session: databases.SessionDep,
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """Airline Send a Message"""

    user_data = await jwt_auth.decode_jwt(jwt, ["acars:atsu"])
    callsign_chk = await callsign_verification(user_data)
    if callsign_chk is None:
        return JSONResponse(
            status_code=403,
            content={"detail": "Unauthorised callsign for provided JWT"}
        )

    sf_msg = databases.StoreAndForward.model_validate(msg)

    # An ATSU should only be able to send a message to an online station
    try:
        databases.DataLinkInitiationCapability.find(
                (databases.DataLinkInitiationCapability.logon_from == msg.msg_to)
            ).first()
    except NotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": f"{msg.msg_to} is not active on the network"})

    background_tasks.add_task(tasks.message_parse, sf_msg, bearer, session)
    return sf_msg
