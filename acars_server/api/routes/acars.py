"""
ACARS Server
ACARS Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from typing import Annotated, Any, Dict, List

# Third Party Libraries
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

# Local Libraries
from acars_server import common, databases, static_data, tasks
from acars_server.api.services.auth_services import (
    callsign_verification,
    jwt_auth
    )

router = APIRouter()
# ------------------------------------------------------------------
# ACARS Endpoints
# ------------------------------------------------------------------
class ResponsePoll(BaseModel):
    """A quick class for responses to a poll message"""
    message_count: int
    message: List[databases.StoreAndForward]

@router.post(
        "/poll",
        responses=static_data.COMMON_ERRORS,
        response_model=ResponsePoll,
        summary="Poll for new messages",
        description=("JWT Audience: [\"acars:aircraft\"]<br />"
                     "Allows an aircraft endpoint to poll the server and request "
                     "any pending messages to be sent. Messages will be sent as a "
                     "list of StoreAndForward objects.")
        )
async def poll_for_new_messages(
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)
    ) -> Response:
    """
    Poll for new messages
    """

    user_data = await jwt_auth.decode_jwt(jwt, ["acars:aircraft"])
    callsign = await callsign_verification(user_data)

    # If the callsign has been validated
    if callsign:
        update_msg = {
            "relayed": True,
            "relayed_at": dt.now(tz.utc).timestamp()
        }
        all_messages = (databases.StoreAndForward.find(
                (databases.StoreAndForward.msg_to == callsign)
                # needs this declaration (== False ! is False) for redis to work
                & (databases.StoreAndForward.relayed == False)
            ).all()
        ) or []
        if len(all_messages) > 0:
            rtn:Dict[str, Any] = {"message_count": len(all_messages), "messages": []}
            update_id_list = []
            for msg in all_messages:
                update_id_list.append(msg["pk"])
                rtn["messages"].append(msg.model_dump())

            if len(update_id_list) > 0:
                records = databases.StoreAndForward.find(
                    (databases.StoreAndForward.msg_to == callsign)
                    & (databases.StoreAndForward.pk << update_id_list)
                ).all()

                for record in records:
                    for k, v in update_msg.items():
                        setattr(record, k, v)
                    record.save()
                    common.logger.success(f"Message retrieved for {callsign} - {record}")
            return JSONResponse(content=rtn)
        common.logger.success(f"No messages to retrive for {callsign}")
        return JSONResponse(content={"msg_count": 0})
    error = ("Unable to retrieve callsign for user - Network: "
                f"{user_data['network']}, User ID: {user_data['uid']}")
    common.logger.error(error)
    return JSONResponse(status_code=403, content = {"error": error})

@router.get(
        "/connect.html",
        status_code=202,
        tags=["Legacy Messaging"],
        summary="Legacy message send with url parameters (Hoppie)",
        description=("JWT Audience: [\"acars:aircraft\"]<br />"
                     "<i>DEPRECEATED:</i> Use /acars/tx endpoint<br />"
                    "Provides a psudo html endpoint for legacy clients. "
                    "Connects directly to the <b>/acars/tx</b> endpoint"
                    ),
        deprecated=True)
async def hoppie_formated_url(
    api_key: Annotated[
        str,
        Query(
            alias="logon",
            description=("This value can be set to anything as authentication is handled "
                         "with the issued JWT. This is only here as a placeholder for "
                         "backwards compatability."))
            ],
    msg_from: Annotated[
        str,
        Query(
            alias="from",
            description="Validation will fail if this doesn't match the user's callsign")],
    msg_to: Annotated[
        str, Query(alias="to", description="The callsign the message should be sent to.")],
    msg_type: Annotated[static_data.MessageTypes, Query(alias="type")],
    packet: Annotated[str, Query(alias="packet", description="Limited to 500 characters")],
    background_tasks: BackgroundTasks,
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """
    Hoppie formatted URL params
    """
    _noop = api_key
    msg = {
        "msg_from": msg_from,
        "msg_to": msg_to,
        "msg_type": msg_type,
        "packet": packet,
        "created": dt.now(tz.utc).timestamp(),
        "network": "vatsim"
    }
    sf_msg = databases.StoreAndForward.model_validate(msg)
    await transmit_a_message(
        msg=sf_msg,
        bearer="fans_vhf",
        background_tasks=background_tasks,
        jwt=jwt)

@router.post(
        "/tx/{bearer}",
        status_code=202,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.StoreAndForward,
        summary="Send a message to the store and forward",
        description=("JWT Audience: [\"acars:aircraft\"]<br />"
                     "<b>CPDLC Message Type</b><br />"
                     "<code>{MSG_ID:int}/{RESPONSE_ID:int|none}/{TIMESTAMP:%y%m%d%H%M%S}"
                     "/{ACK:str}/{MESSAGE:str}</code><br />"
                     "MESSAGE should contain DM/UM codes only. Any data fields should follow in "
                     "order delimted by ','<br />Example: <code>4/3/260621215400/N/DM104,ABEVI,"
                     "1430</code> or <code>7/6/260621215512/WU/DM11,POL,FL240</code>"
                    ),
        )
async def transmit_a_message(
    msg:databases.StoreAndForward,
    bearer: static_data.BearerTypes,
    background_tasks: BackgroundTasks,
    session: databases.SessionDep,
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """
    Allow an aircraft to transmit a message
    """

    user_data = await jwt_auth.decode_jwt(jwt, ["acars:aircraft"])
    callsign = await callsign_verification(user_data)
    sf_msg = databases.StoreAndForward.model_validate(msg)

    # If the callsign has been validated
    if callsign:
        background_tasks.add_task(tasks.message_parse, sf_msg, bearer, session)
        return JSONResponse(status_code=202, content=sf_msg.model_dump_json())

    error = (f"Callsign validation failed - Network: {user_data['network']}, "
             f"User ID: {user_data['uid']}, Callsign: {sf_msg['msg_from']}")
    common.logger.error(error)
    return JSONResponse(status_code=403, content={"error": error})
