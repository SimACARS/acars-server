"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import ast

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
    if msg["msg_type"] == "inforeq" and str(msg["packet"]).startswith("ATIS"):
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

    # Validate the message content
    sf_msg = sql.StoreAndForward.model_validate(t_msg)

    # Commit the message to the store
    session.add(sf_msg)
    session.commit()
    session.refresh(sf_msg)
