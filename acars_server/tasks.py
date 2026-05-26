"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import ast
import re
from typing import Any, Dict, Union

# Third Party Libraries
from datetime import datetime as dt, timezone as tz
from loguru import logger

# Local Libraries
from acars_server import inforeq, sql


vs = inforeq.Vatsim()

def message_parse(msg:sql.StoreAndForward, session:sql.SessionDep):
    """Parse a message"""
    send_msg:Dict[str, Any] = {"packet" : None}

    # INFOREQ ATIS
    if msg["msg_type"] == "inforeq":
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

    # Validate the message content
    if send_msg["packet"] is None:
        sf_msg = sql.StoreAndForward.model_validate(msg)
    else:
        sf_msg = sql.StoreAndForward.model_validate(send_msg)

    # Commit the message to the store
    session.add(sf_msg)
    session.commit()
    session.refresh(sf_msg)
