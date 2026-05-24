"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import queue
from typing import Annotated

# Third Party Libraries
from pydantic import AfterValidator, BaseModel

# Local Libraries
from acars_server import static_data

def check_valid_oooi_smi_type(smi_type: str):
    """Check if the provided SMI code is valid"""
    if not static_data.OOOI_SMI_TYPES.get(smi_type):
        raise ValueError(f"Invalid SMI Type. Valid types are: {' '.join(static_data.OOOI_SMI_TYPES.keys())}")
    return smi_type

def check_valid_legacy_msg_type(legacy_type: str):
    """Check if the message type is valid"""
    if legacy_type not in static_data.LEGACY_MSG_TYPES:
        raise ValueError(f"Invalid message type: Valid types are: {' '.join(static_data.LEGACY_MSG_TYPES)}")
    return legacy_type


class MsgOooi(BaseModel):
    """Progress Message"""
    sending_station: str
    receiving_station: str
    msg_header: str
    msg_smi: Annotated[str, AfterValidator(check_valid_oooi_smi_type)]
    msg_fi: str
    msg_dt: str


class LegacyMessage(BaseModel):
    """Legacy Messages"""
    logon: str
    msg_from: str
    msg_to: str
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)]
    packet: str
