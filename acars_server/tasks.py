"""
ACARS Server
Background Tasks
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import ast
import re
from typing import Any, Dict

# Third Party Libraries
from datetime import datetime as dt, timezone as tz

# Local Libraries
from acars_server import common, inforeq, sql


vs = inforeq.Vatsim()

def message_parse(msg:sql.StoreAndForward, session:sql.SessionDep):
    """Parse a message"""
    common.logger.debug("Message Parser")
    send_msg:Dict[str, Any] = {"packet" : None}

    # INFOREQ ATIS
    if msg["msg_type"] == "inforeq":
        send_msg = msg_type_inforeq(msg)
    # ADS-C
    elif msg["msg_type"] == "ads-c":
        if not msg_type_ads_c(msg):
            return
    # CPDLC
    elif msg["msg_type"] == "cpdlc":
        if not msg_type_cpdlc(msg):
            return

    # Validate the message content
    if send_msg["packet"] is None:
        sf_msg = sql.StoreAndForward.model_validate(msg)
    else:
        sf_msg = sql.StoreAndForward.model_validate(send_msg)

    # Commit the message to the store
    session.add(sf_msg)
    session.commit()
    session.refresh(sf_msg)

def msg_type_ads_c(msg:sql.StoreAndForward) -> bool:
    """Validates ADS-C messages"""
    if re.match(r"^REPORT\s[A-Z0-9]{4,10}\s\d{6}\s[\d\.\-]+\s[\d\.\-]+\s\d{1,6}$", msg["packet"]):
        return True
    return False

def msg_type_cpdlc(msg:sql.StoreAndForward) -> bool:
    """Validates CPDLC messages"""
    if re.match(r"^\/data2\/\d+\/\d*\/[A-Z]{0,2}\/.*$", msg["packet"]):
        return True
    return False

def msg_type_inforeq(msg:sql.StoreAndForward) -> Dict[str, Any]:
    """Handle INFOREQ messages"""
    send_msg = {
        "created": dt.now(tz.utc).timestamp(),
        "msg_type": "telex",
        "network": msg["network"],
        "packet": None,
        "msg_to": msg["msg_from"],
        "msg_from": "SYSTEM"
    }

    if (msg["msg_type"] == "inforeq" and
        str(msg["packet"]).startswith("ATIS") and
        re.match(r"^[A-Z]{4}(_[AD])?$", msg["msg_to"])):

        if msg["network"] == "vatsim":
            # Attempt to pull the ATIS
            response = vs.get_atis(msg["msg_to"])

            # Deal with a vATIS oddity in returning something that looks like a list but isn't
            if response.startswith("["):
                fmt = ast.literal_eval(response)
                send_msg["packet"] = "@".join(fmt)
            else:
                send_msg["packet"] = response

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("METAR") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        if msg["network"] == "vatsim":
            send_msg["packet"] = inforeq.Vatsim.get_metar(msg["msg_to"])
        else:
            send_msg["packet"] = inforeq.Noaa.metar(msg["msg_to"])

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("TAF") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        send_msg["packet"] = inforeq.Noaa.taf(msg["msg_to"])

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("SHORTTAF") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        send_msg["packet"] = inforeq.Noaa.shorttaf(msg["msg_to"])

    return send_msg
