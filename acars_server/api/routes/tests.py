"""
ACARS Server
Test Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from typing import Any, Dict

# Third Party Libraries
from fastapi import APIRouter, BackgroundTasks, Response
from fastapi.responses import JSONResponse

# Local Libraries
from acars_server import auth, common, databases, tasks

router = APIRouter()
# ------------------------------------------------------------------
# Test Endpoints
# ------------------------------------------------------------------
@router.get(
        "/auth/new_user/{cid}",
        response_model=databases.ApiKeyPublic)
async def test_auth_new_user(
    cid:str,
    session: databases.SessionDep
    ):
    """Creates a test user for testing purposes. Not to be used in production"""
    # Generate the API key using the cid
    api_key = auth.Auth().api_key_generator(cid, "testing")

    # Add the API key to the DB
    dtnow = dt.now(tz.utc).timestamp()
    db_data = {
        "api_key": api_key,
        "network": "testing",
        "created": dtnow,
        "last_used": dtnow
    }
    db_add = databases.ApiKey.model_validate(db_data)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return db_add

@router.get("/poll/{callsign}")
async def test_poll(callsign:str) -> Response:
    """Test POLL"""
    # If the callsign has been validated
    update_msg = {
        "relayed": True,
        "relayed_at": dt.now(tz.utc).timestamp()
    }
    all_messages = databases.StoreAndForward.find(
                (databases.StoreAndForward.msg_to == callsign)
                & (databases.StoreAndForward.relayed == "0")
            ).all()
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

@router.get("/{ir_type}/{network}/{station}", status_code=204)
async def test_inforeq(
    ir_type:str,
    network:str,
    station:str,
    background_tasks: BackgroundTasks,
    ):
    """INFOREQ Test"""
    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "msg_type": "inforeq",
        "network": network,
        "packet": ir_type.upper(),
        "msg_to": station,
        "msg_from": "TEST1"
    }
    sf_msg = databases.StoreAndForward.model_validate(t_msg)
    common.logger.success(sf_msg)
    background_tasks.add_task(tasks.message_parse, sf_msg)
    return JSONResponse(content={"status": "ok"})

@router.post("/tx", status_code=204)
async def test_tx(
    msg:databases.StoreAndForward,
    background_tasks: BackgroundTasks,
    ):
    """INFOREQ Test"""
    sf_msg = databases.StoreAndForward.model_validate(msg)
    t_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "msg_type": sf_msg["msg_type"],
        "network": sf_msg["network"],
        "packet": sf_msg["packet"],
        "msg_to": sf_msg["msg_to"],
        "msg_from": sf_msg["msg_from"]
    }
    sf2_msg = databases.StoreAndForward.model_validate(t_msg)
    common.logger.success(sf2_msg)
    background_tasks.add_task(tasks.message_parse, sf2_msg)
    return JSONResponse(content={"status": "ok"})
