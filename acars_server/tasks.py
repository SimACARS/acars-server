"""
ACARS Server
Background Tasks
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import ast
import re
from datetime import datetime as dt, timezone as tz
from typing import Any, Dict

# Third Party Libraries

# Local Libraries
from acars_server import common, databases, functions
from acars_server.api.message_types import adexp, inforeq


vs = inforeq.Vatsim()


class TransmissionDelay:
    """Transmission Delay"""
    @staticmethod
    async def fans_hf() -> None:
        """FANS 1/A HFDL - 60s to 90s - 1.8kbps"""
        timer = random.randint(60,90)
        sleep(timer)

    @staticmethod
    async def fans_vhf() -> None:
        """FANS 1/A VHF - 4s to 10s - 2.4kbps"""
        timer = random.randint(4,10)
        sleep(timer)

    @staticmethod
    async def fans_satcom() -> None:
        """FANS 1/A SATCOM - 30s to 45s"""
        timer = random.randint(30,45)
        sleep(timer)

    @staticmethod
    async def atn_vhf() -> None:
        """ATN VHF - 1s to 4s - 31.5kbps"""
        timer = random.randint(1,4)
        sleep(timer)

    @staticmethod
    async def atn_satcom() -> None:
        """ATN SATCOM - 10s to 20s"""
        timer = random.randint(10,20)
        sleep(timer)


async def message_parse(msg:databases.StoreAndForward):
    """Parse a message"""
    common.logger.debug("Message Parser")
    send_msg:Dict[str, Any] = {"packet" : None}

    # INFOREQ ATIS
    if msg["msg_type"] == "inforeq":
        send_msg = msg_type_inforeq(msg)
    # ADS-C
    elif msg["msg_type"] == "ads-c": # pragma: no cover
        if not msg_type_ads_c(msg):
            return
    # CPDLC
    elif msg["msg_type"] == "cpdlc": # pragma: no cover
        if not msg_type_cpdlc(msg):
            return
    # ADEXP
    elif msg["msg_type"] == "adexp": # pragma: no cover
        adexp_msg = adexp.Adexp(msg)
        if not msg_type_cpdlc(msg):
            return

    # Validate the message content
    if send_msg["packet"] is None:
        sf_msg = databases.StoreAndForward.model_validate(msg)
    else:
        sf_msg = databases.StoreAndForward.model_validate(send_msg)

    # Always save to the 24hr message store for visability
    sf_msg.save()
    databases.redis_db.expire(
        sf_msg.key(),
        86400,
    )

    # Commit the message to the relevant stream
    stream = None
    if sf_msg.relayed:
        sf_msg.relayed = 1
    else:
        sf_msg.relayed = 0

    if str(sf_msg.msg_to).startswith("_COY_"):
        stream = f"msg:coy:{sf_msg.network}:{sf_msg.msg_to}"
    elif str(sf_msg.msg_to).startswith("_ATC_"):
        stream = f"msg:atc:{sf_msg.network}:{sf_msg.msg_to}"

    if stream is not None:
        group = f"sse:{sf_msg.network}:{sf_msg.msg_to}"
        common.logger.debug(f"Adding message to stream: {stream} {sf_msg.model_dump()}")
        await functions.ensure_group_once(databases.redis_async_db, stream, group)
        await databases.redis_async_db.xadd(stream, sf_msg.model_dump())

def msg_type_ads_c(msg:databases.StoreAndForward) -> bool:
    """Validates ADS-C messages"""
    if re.match(r"^REPORT\s[A-Z0-9]{4,10}\s\d{6}\s[\d\.\-]+\s[\d\.\-]+\s\d{1,6}$", msg["packet"]):
        return True
    return False

def msg_type_cpdlc(msg:databases.StoreAndForward) -> bool:
    """Validates CPDLC messages"""
    if re.match(r"^\/data2\/\d+\/\d*\/[A-Z]{0,2}\/.*$", msg["packet"]):
        return True
    return False

def msg_type_inforeq(msg:databases.StoreAndForward) -> Dict[str, Any]:
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
