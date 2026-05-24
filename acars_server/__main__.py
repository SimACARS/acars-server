"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Annotated

# Third Party Libraries
from fastapi import FastAPI
from loguru import logger

# Local Libraries
from acars_server import message_types

app = FastAPI()


@app.get("/")
async def read_root():
    """Root"""
    return {"Hello": "World"}

@app.get("/msg/get/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Progress"""
    return {"item_id": item_id, "q": q}

@app.post("/msg/post/oooi")
async def post_msg_progress(msg: message_types.MsgOooi):
    """Post a message"""

    return {"msg_from": msg.sending_station, "msg_to": msg.receiving_station, "msg": msg.msg_smi}

@app.post("/msg/legacy")
async def legacy_message(msg: message_types.LegacyMessage):
    """Legacy message"""
    return msg.msg_from
