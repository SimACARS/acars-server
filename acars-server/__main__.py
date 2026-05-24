"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import queue
from typing import Annotated

# Third Party Libraries
from fastapi import FastAPI
from loguru import logger
from pydantic import AfterValidator, BaseModel

# Local Libraries

app = FastAPI()

# Ref: https://www.oag.com/hubfs/Inbound-Services/OAG-ACARS-OOOI-Message-Types-and-Examples.pdf
OOOI_SMI_TYPES = {
    "AEP": "POSITION REPORT WITH WEATHER INFORMATION",
    "AGM": "MISCELLANEOUS AG MESSAGE",
    "ALR": "ALERT MESSAGE",
    "ARR": "ARRIVAL REPORT",
    "DEP": "DEPARTURE REPORT",
    "DLA": "FLIGHT DELAY",
    "ETA": "ESTIMATED TIME OF ARRIVAL",
    "GVR": "GROUND ORIGINATED VOICE REQUEST",
    "POS": "POSITION REPORT WITHOUT WEATHER INFORMATION"
}

def check_valid_oooi_smi_type(smi_type: str):
    """Check if the provided SMI code is valid"""
    if not OOOI_SMI_TYPES.get(smi_type):
        raise ValueError(f"Invalid SMI Type. Valid types are: {' '.join(OOOI_SMI_TYPES.keys())}")
    return smi_type

class MsgOooi(BaseModel):
    """Progress Message"""
    sending_station: str
    receiving_station: str
    msg_header: str
    msg_smi: Annotated[str, AfterValidator(check_valid_oooi_smi_type)]
    msg_fi: str
    msg_dt: str


""" 
"progress",
"cpdlc",
"telex",
"ping",
"posreq",
"position",
"datareq",
"poll",
"peek"
"""

"""
Possibly use OAUTH with Vatsim to link CID to API key to authenticate the sending callsign
Essentially a one time link when registering...
"""

@app.get("/")
async def read_root():
    """Root"""
    return {"Hello": "World"}

@app.get("/msg/get/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    """Progress"""
    return {"item_id": item_id, "q": q}

@app.post("/msg/post/oooi")
async def post_msg_progress(msg: MsgOooi):
    """Post a message"""

    return {"msg_from": msg.sending_station, "msg_to": msg.receiving_station, "msg": msg.msg_smi}
