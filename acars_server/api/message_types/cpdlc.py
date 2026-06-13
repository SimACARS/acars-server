"""
ACARS Server
CDPLC Validation
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from datetime import datetime, timezone
from typing import Any, Dict, Union

# Third Party Libraries
from loguru import logger
from sqlmodel import select, Session

# Local Libraries
from acars_server import common, databases, static_data

# Message format
# https://ext.eurocontrol.int/WikiLink/images/2/28/Link-2000-guidance-to-ground-implementers.pdf
# p57-58
# {MSG_ID}/{RESPONSE_ID}/{TIMESTAMP - YYMMDDHHMMSS}/{LOGICAL ACKNOWLEDGEMENT}/{MESSAGE}
# {MSG_ID} assigned by the sending system sequentially and per destination
# {RESPONSE_ID} for response messages only. The message reference number of a response message shall
#   be identical to the message identification number of the received message to which it responds
# {TIMESTAMP} the time the message is dispatched by the originating user. It consists of the date
#   (YYMMDD) and time (HHMMSS).
# {LOGICAL ACKNOWLEDGEMENT} Indicates whether a logical acknowledgement (LACK) is required for the
#   message. The ACL, ACM require a LACK for all messages (except for ERROR and LACK messages).


# 'Hoppie' format (not really Hoppie but commonly used on that network)
# /data2/{MSG_ID}/{RESPONSE_ID}/{RESPONSE_TYPE}/{MESSAGE}


class Cpdlc:
    """A CPDLC Class"""

    def __init__(self, message:databases.StoreAndForward) -> None:
        self.message = message
        self.exploded:Dict[str, Any] = {}

    def _msg_type_cpdlc(self) -> re.Match[str]|None:
        """Validates CPDLC messages"""
        data_check = re.match(
            r"^(\d+)\/(\d+)\/([23]\d[01]\d[0-3]\d[0-2]\d[0-6]\d[0-6]\d)\/([A-Z]*)\/(.*)$",
            self.message.packet)
        if data_check:
            logger.debug(data_check)
            return data_check

        common.logger.error(
            f"CPDLC: Invalid Format. Expected ^/data2/d+/d*/[A-Z]{0,2}/.*$ - {self.message}")
        return None

    def parse_message(self) -> None:
        """Breaks the message up into logical parts"""
        chk = self._msg_type_cpdlc()
        if chk:
            is_uplink = False
            if re.match(r"\d+", chk.group(1)) and chk.group(2) == "":
                is_uplink = True

            dt = datetime.strptime(chk.group(3), "%y%m%d%H%M%S")
            dtu = dt.replace(tzinfo=timezone.utc)
            dts = dtu.timestamp()

            self.exploded = {
                "tx_id": chk.group(1),
                "responding_to_id": chk.group(2),
                "msg_timestamp": dts,
                "response_type_required": chk.group(4),
                "content": chk.group(5),
                "is_uplink": is_uplink,
                "msg_to": str(self.message.msg_to),
                "msg_from": str(self.message.msg_from)
            }

    def message_validation(
            self,
            session:databases.SessionDep) -> None:
        """Validates a message"""
        rtn:Dict[str, Any] = {}
        # Check that the message contains a UM or DM code
        content_val = re.match(r"^([UD]M[0-9]{1,3}[a-z]{0,2})(.*)", self.exploded["content"])
        logger.debug(content_val)
        if content_val:
            # Lookup the UM or DM code to validate it
            lookup = select(
                databases.CPDLCTypes).where(
                    databases.CPDLCTypes.reference_number == content_val.group(1))
            logger.debug(f"\n{lookup}")
            result = session.exec(lookup).first()
            logger.debug(result)
            if result:
                rtn["ref"] = result.reference_number
                rtn["variables"] = {}
                # Look for any variables in the message element. Indicated by [ ]
                matches = re.findall(r"\[([^\]]+)\]", result.message_element)
                logger.debug(matches)
                if matches:
                    ordered_match_set = list(dict.fromkeys(matches))
                    logger.debug(ordered_match_set)
                    split_content = content_val.group(2).split(",")
                    logger.debug(split_content)

                    for match, sc in zip(ordered_match_set, split_content[1:]):
                        logger.debug(f"{match} {sc}")
                        rtn["variables"][match] = sc

        # Overwrite data with validated message
        self.exploded["content"] = rtn

    def response_id_checker(self):
        """Checks that the responding_to_id is valid"""

    def response_type_required_check(self) -> Dict[str, Union[str, Any]]:
        """Checks that the response_required is valid"""
        # Format the response
        response_required = str(self.exploded["response_type_required"])
        r_chk = response_required.replace("/", "_")

        # Select the correct responses depending on if this is an uplink msg or not
        if self.exploded["is_uplink"]:
            message_stack = static_data.CPDLC_UPLINK_MESSAGE_RESPONSES
            direction = "uplink"
        else:
            message_stack = static_data.CPDLC_DOWNLINK_MESSAGE_RESPONSES
            direction = "downlink"

        if message_stack.get(r_chk):
            rtn = message_stack[r_chk]
            common.logger.success(f"CPDLC: Valid {direction} message - {rtn}")
            return rtn

        common.logger.error(
            f"CPDLC: Invalid {direction} response format. - {response_required}")
        return {"data": "ERROR"}

m = {
    "msg_from": "RFI221B",
    "msg_to": "_ATC_EGKK",
    "msg_type": "cpdlc",
    "packet": "1/1/260613182500/N/DM109,1423",
    "network": "vatsim",
    "created": datetime.now(tz=timezone.utc).timestamp()
}
m_val = databases.StoreAndForward.model_validate(m)
logger.debug(m_val.model_dump())

c = Cpdlc(m_val)
c.parse_message()
logger.debug(c.exploded)
with Session(databases.engine) as s:
    c.message_validation(s)
logger.debug(c.exploded)
