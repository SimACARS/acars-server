"""
ACARS Server
CDPLC Validation
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from typing import Any, Dict, Union

# Third Party Libraries

# Local Libraries
from acars_server import common, sql, static_data

# Message format
# /data2/{MSG_ID}/{RESPONSE_ID}/{RESPONSE_TYPE}/{MESSAGE}


class Cpdlc:
    """A CPDLC Class"""

    def __init__(self, message:sql.StoreAndForward) -> None:
        self.message = message
        self.exploded:Dict[str, Union[str,bool]] = {}

    def _msg_type_cpdlc(self) -> bool:
        """Validates CPDLC messages"""
        if re.match(r"^\/data2\/\d+\/\d*\/[A-Z]{0,2}\/.*$", self.message["packet"]):
            return True
        common.logger.error(
            f"CPDLC: Invalid Format. Expected ^/data2/d+/d*/[A-Z]{0,2}/.*$ - {self.message}")
        return False

    def explode_message(self) -> None:
        """Breaks the message up into logical parts"""
        if self._msg_type_cpdlc():
            ex_msg = str(self.message).split("/")
            is_uplink = False
            if re.match(r"\d+", ex_msg[1]) and ex_msg[2] == "":
                is_uplink = True

            self.exploded = {
                "data": ex_msg[0],
                "tx_id": ex_msg[1],
                "responding_to_id": ex_msg[2],
                "response_type_required": ex_msg[3],
                "content": ex_msg[4],
                "is_uplink": is_uplink,
                "msg_to": str(self.message.msg_to),
                "msg_from": str(self.message.msg_from)
            }

    def response_id_checker(self) -> bool:
        """Checks that the responding_to_id is valid"""
        return False

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
