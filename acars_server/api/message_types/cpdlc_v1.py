"""
ACARS Server
CDPLC Validation
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import re
from typing import Literal

# Third Party Libraries

# Local Libraries

CPDLC_USER_ABORT_REASON = [
    "undefined",
    "no message identification numbers available",
    "duplicate message identification numbers",
    "no longer next data authority",
    "current data authority abort",
    "commanded termination",
    "invalid response",
    "time out of synchronisation",
    "unknown integrity check",
    "validation failure",
    "unable to decode message",
    "invalid pdu",
    "invalid cpdlc message"
]

CPDLC_PROVIDER_ABORT_REASON = [
    "timer expired",
    "undefined error",
    "invalid pdu",
    "protcol error",
    "communication service error",
    "communication service failure",
    "invalid qos parameter",
    "expected pdu missing"
]

def ia5_regex(length_from: int, length_to:int=0):
    """IA5 String"""
    if length_from <= 0:
        pattern = rf"^[\x20-\x7E]{{{length_from}}}$"
    else:
        pattern = rf"^[\x20-\x7E]{{{length_from},{length_to}}}$"
    return re.compile(pattern)


class CpldcTypes:
    """CPDLC Types"""

    @staticmethod
    def aircraft_address(data:str) -> str:
        """
        Aircraft Address
        BIT STRING (SIZE(24))
        """
        chk = re.match(r"[A-F0-9]{24}", data.upper())
        if chk:
            return chk.group(1)
        raise ValueError("Expected STRING (SIZE(24))")

    @staticmethod
    def aircraft_flight_identification(data:str) -> str:
        """
        Aircraft Flight Identification
        IA5 STRING (SIZE(2,8))
        """
        chk = re.match(ia5_regex(2,8), data.upper())
        if chk:
            return chk.group(1)
        raise ValueError("Expected IA5 STRING (SIZE(2,8))")

    @staticmethod
    def airport(data:str) -> str:
        """
        Airport
        IA5 STRING (SIZE(4))
        """
        chk = re.match(ia5_regex(4), data.upper())
        if chk:
            return chk.group(1)
        raise ValueError("Expected IA5 STRING (SIZE(4))")

    def altimeter(
            self, data:int, data_type:Literal["altimeter_english", "altimeter_metric"]) -> int:
        """
        Altimeter
        CHOICE
        """
        if data_type == "altimeter_english":
            return self.altimeter_english(data)
        if data_type == "altimeter_metric":
            return self.altimeter_metric(data)
        raise ValueError("Expected IA5 STRING (SIZE(4))")

    @staticmethod
    def altimeter_english(data:int) -> int:
        """
        Altimeter English (inHg)
        INTEGER (2200,3200) (resolution 0.01)
        """
        if 2200 < data < 3200:
            return data
        raise ValueError("Expected INTEGER (2200,3200)")

    @staticmethod
    def altimeter_metric(data:int) -> int:
        """
        Altimeter Metric (HPa)
        INTEGER (7500,12500) (resolution 0.01)
        """
        if 7500 < data < 12500:
            return data
        raise ValueError("Expected INTEGER (2200,3200)")

    @staticmethod
    def atis_code(data:str) -> str:
        """
        ATIS Code
        IA5 STRING (SIZE(1))
        """
        chk = re.match(ia5_regex(1), data.upper())
        if chk:
            return chk.group(1)
        raise ValueError("Expected IA5 STRING (SIZE(1))")

    @staticmethod
    def ats_route_designator(data:str) -> str:
        """
        ATS Route Designator
        IA5 STRING (SIZE(2,7))
        """
        chk = re.match(ia5_regex(2,7), data.upper())
        if chk:
            return chk.group(1)
        raise ValueError("Expected IA5 STRING (SIZE(2,7))")

    def atw_along_track_waypoint(self, position, atw_distance, speed, atw_level):
        """
        Along Track Waypoint
        SEQUENCE
        """
        ...
