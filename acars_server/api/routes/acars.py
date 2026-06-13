"""
ACARS Server
ACARS Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from typing import Annotated, Any, Dict

# Third Party Libraries
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from redis import ResponseError

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
@router.post("/poll", responses=static_data.COMMON_ERRORS)
async def poll_for_new_messages(
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)
    ) -> Response:
    """
    Poll for new messages
    \nJWT Audience: ["acars:aircraft"]
    """

    user_data = await jwt_auth.decode_jwt(jwt, ["acars:aircraft"])
    callsign = await callsign_verification(user_data)

    # If the callsign has been validated
    if callsign:
        update_msg = {
            "relayed": True,
            "relayed_at": dt.now(tz.utc).timestamp()
        }
        try:
            all_messages = databases.StoreAndForward.find(
                        (databases.StoreAndForward.msg_to == callsign)
                        # needs this declaration (== False ! is False) for redis to work
                        & (databases.StoreAndForward.relayed == False)
                    ).all()
        except ResponseError:
            return JSONResponse(content={"msg_count": 0})
        if len(all_messages) > 0:
            rtn:Dict[str, Any] = {"message_count": len(all_messages), "messages": []}
            update_id_list = []
            for m in all_messages:
                update_id_list.append(m["pk"])
                data_block = {
                    "pk": m["pk"],
                    "msg_from": m["msg_from"],
                    "msg_to": m["msg_to"],
                    "msg_type": m["msg_type"],
                    "packet": m["packet"],
                    "network": m["network"]
                }
                rtn["messages"].append(data_block)

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
            return JSONResponse(rtn)
        common.logger.success(f"No messages to retrive for {callsign}")
        return JSONResponse(content={"msg_count": 0})
    error = ("Unable to retrieve callsign for user - Network: "
                f"{user_data['network']}, User ID: {user_data['uid']}")
    common.logger.error(error)
    return JSONResponse(status_code=403, content = {"error": error})

@router.get("/connect.html", tags=["Legacy Messaging"], deprecated=True)
async def hoppie_formated_url(
    api_key: Annotated[str, Query(alias="logon")],
    msg_from: Annotated[str, Query(alias="from")],
    msg_to: Annotated[str, Query(alias="to")],
    msg_type: Annotated[str, Query(alias="type")],
    packet: Annotated[str, Query(alias="packet")],
    background_tasks: BackgroundTasks,
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """
    Provides a psudo html endpoint for legacy clients.
    Connects directly to the <b>/msg/legacy/tx</b> endpoint
    \nJWT Audience: ["acars:aircraft"]
    """
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
        background_tasks=background_tasks,
        jwt=jwt)

@router.post(
        "/tx",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.StoreAndForward
        )
async def transmit_a_message(
    msg:databases.StoreAndForward,
    background_tasks: BackgroundTasks,
    jwt:HTTPAuthorizationCredentials = Depends(common.header_bearer)):
    """
    Allow an aircraft to transmit a message
    \nJWT Audience: ["acars:aircraft"]
    \n\tMessage Type:cpdlc
    \n\tPacket:str (separated by '/'): 
    \n\t\t{MSG_ID:int}/{RESPONSE_ID:int|none}/{TIMESTAMP:%y%m%d%H%M%S}/{ACK:str}/{MESSAGE:str}
    \n\t\tMESSAGE DM/UM codes only. Any data fields should follow in order delimted by ','
    \n\t\texample: DM104,ABEVI,1430 or DM11,POL,FL240
    """

    user_data = await jwt_auth.decode_jwt(jwt, ["acars:aircraft"])
    callsign = await callsign_verification(user_data)
    sf_msg = databases.StoreAndForward.model_validate(msg)

    # If the callsign has been validated
    if callsign:
        background_tasks.add_task(tasks.message_parse, sf_msg)
        return sf_msg

    error = (f"Callsign validation failed - Network: {user_data['network']}, "
             f"User ID: {user_data['uid']}, Callsign: {sf_msg['msg_from']}")
    common.logger.error(error)
    return JSONResponse(status_code=403, content={"error": error})
