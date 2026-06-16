"""
ACARS Server
CDPLC Validation
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import base64
import re
from datetime import datetime, timezone
from typing import Any, Dict, Union

# Third Party Libraries
from loguru import logger
from redis_om.model.model import NotFoundError # type: ignore
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

    def run(self) -> Dict[str, Union[str, Any]]:
        """Runs all checks"""
        self.parse_message()
        with Session(databases.engine) as s:
            self.message_validation(s)
        #self.message_transaction_state()
        return self.response_type_required_check()

    def _msg_type_cpdlc(self) -> re.Match[str]|None:
        """Validates CPDLC messages"""
        data_check = re.match(
            r"^(\d+)\/(\d*)\/([23]\d[01]\d[0-3]\d[0-2]\d[0-6]\d[0-6]\d)\/([A-Z]*)\/(.*)$",
            self.message.packet)
        if data_check:
            logger.debug(data_check)
            return data_check

        common.logger.error(
            f"CPDLC: Invalid Format - {self.message}")
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
            return
        raise ValueError("Unknown message type")

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

    def message_transaction_state(self):
        """Maintains a state between two stations"""
        if self.message.msg_from.startswith("_ATC_"):
            atsu = self.message.msg_from
            aircraft = self.message.msg_to
        elif self.message.msg_to.startswith("_ATC_"):
            atsu = self.message.msg_to
            aircraft = self.message.msg_from
        else:
            raise ValueError("Unexpected prefix. Expected _ATC_")

        # Generate a transaction string
        transaction_string = f"{self.message.network}:{aircraft}:{atsu}"
        transaction = base64.urlsafe_b64encode(transaction_string.encode())

        rtn_msg = {
            "transaction_str": str(transaction)
        }

        try:
            # Test to see if transaction is already live
            check_if_current = databases.CpdlcConnectionStateStore.find(
                        (databases.CpdlcConnectionStateStore.transaction_str == transaction)
                    ).first()
            expected_id = check_if_current.expected_next_tx_id
        except NotFoundError:
            # If this is a new transaction and ATC are trying to initiate, then deny
            if self.message.msg_from.startswith("_ATC_"):
                raise ValueError("No live transaction. ATC cannot initiate unsolicitated CPDLC")
            # If no live transaction, then this is the first message
            expected_id = 1

        # If ID is out of sequence then deny
        if expected_id != self.exploded["tx_id"]:
            raise ValueError(
                f"Unexpected ID {self.exploded['tx_id']} provided. Expected {expected_id}")

        rtn_msg["expected_next_tx_id"] = str(int(expected_id) + 1)

        val_msg = databases.CpdlcConnectionStateStore.model_validate(rtn_msg)
        val_msg.save()
        databases.redis_db.expire(
            val_msg.key(),
            3600,
        )

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
