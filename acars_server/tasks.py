"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import ast
import re

# Third Party Libraries
from datetime import datetime as dt, timezone as tz
from loguru import logger

# Local Libraries
from acars_server import inforeq, sql


vs = inforeq.Vatsim()

def message_parse(msg:sql.StoreAndForward, session:sql.SessionDep):
    """Parse a message"""
    t_msg = msg
    # INFOREQ ATIS
    if (msg["msg_type"] == "inforeq" and
        str(msg["packet"]).startswith("ATIS") and
        re.match(r"[A-Z]{4}", msg["msg_to"])):

        if msg["network"] == "vatsim":
            # Attempt to pull the ATIS
            response = vs.get_atis(msg["msg_to"])

            # Deal with a vATIS oddity in returning something that looks like a list but isn't
            if response.startswith("["):
                fmt = ast.literal_eval(response)
                pkt = "@".join(fmt)
            else:
                pkt = response

            # Format the message to return to the requester
            t_msg = {
                "created": dt.now(tz.utc).timestamp(),
                "msg_type": "inforeq",
                "network": msg["network"],
                "packet": pkt,
                "msg_to": msg["msg_from"],
                "msg_from": "SERVER"
            }

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("METAR") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        if msg["network"] == "vatsim":
            pkt = inforeq.Vatsim.get_metar(msg["msg_to"])
        else:
            pkt = inforeq.Noaa.metar(msg["msg_to"])

        # Format the message to return to the requester
        t_msg = {
            "created": dt.now(tz.utc).timestamp(),
            "msg_type": "inforeq",
            "network": msg["network"],
            "packet": pkt,
            "msg_to": msg["msg_from"],
            "msg_from": "SERVER"
        }

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("TAF") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        pkt = inforeq.Noaa.taf(msg["msg_to"])

        # Format the message to return to the requester
        t_msg = {
            "created": dt.now(tz.utc).timestamp(),
            "msg_type": "inforeq",
            "network": msg["network"],
            "packet": pkt,
            "msg_to": msg["msg_from"],
            "msg_from": "SERVER"
        }

    elif (msg["msg_type"] == "inforeq" and
          str(msg["packet"]).startswith("SHORTTAF") and
          re.match(r"[A-Z]{4}", msg["msg_to"])):

        pkt = inforeq.Noaa.shorttaf(msg["msg_to"])

        # Format the message to return to the requester
        t_msg = {
            "created": dt.now(tz.utc).timestamp(),
            "msg_type": "inforeq",
            "network": msg["network"],
            "packet": pkt,
            "msg_to": msg["msg_from"],
            "msg_from": "SERVER"
        }

    # Validate the message content
    sf_msg = sql.StoreAndForward.model_validate(t_msg)

    # Commit the message to the store
    session.add(sf_msg)
    session.commit()
    session.refresh(sf_msg)
