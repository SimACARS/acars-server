"""
ACARS Server
Static Data Types
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from enum import StrEnum
from typing import Annotated, Any, Dict

# Third Party Libraries
from pydantic import BaseModel, Field

# Local Libraries


class MessageTypes(StrEnum):
    """Message Types"""
    PROGRESS = "progress"
    CPDLC = "cpdlc"
    TELEX = "telex"
    ADEXP = "adexp"
    PING = "ping"
    POSREQ = "posreq"
    POSITION = "position"
    DATAREQ = "datareq"
    POLL = "poll"
    PEEK = "peek"
    INFOREQ = "inforeq"
    ADS_C = "ads-c"


class NetworkTypes(StrEnum):
    """Network Types"""
    VATSIM = "vatsim"
    IVAO = "ivao"
    PILOTEDGE = "pilotedge"
    POSCON = "poscon"
    APOC = "apoc"
    SAYINTENTIONS = "sayintentions"
    OFFLINE = "offline"
    TESTING = "testing"


class SystemConfigTypes(StrEnum):
    """System Config Types"""
    LS_CM_CONTACT = "ls_cm_contact"


class BearerTypes(StrEnum):
    """Bearer Types"""
    FANS_HF = "fans_hf"
    FANS_VHF = "fans_vhf"
    FANS_SATCOM = "fans_satcom"
    ATN_VHF = "atn_vhf"
    ATN_SATCOM = "atn_satcom"


class ResponseJWT(BaseModel):
    """A quick class to return a JWT"""
    exp: Annotated[int, Field(default="<int:Expiry>")]
    nbf: Annotated[int, Field(default="<int:Not Before>")]
    iat: Annotated[int, Field(default="<int:Issued At>")]
    iss: str = "urn:simacars"
    aud: Annotated[str, Field(default="<str:Audience>")]
    network: Annotated[str, Field(default="<str:Network>")]
    loc: Annotated[str, Field(default="<str:Log Off Code>")]
    uid: Annotated[int, Field(default="<int:User ID>")]
    sub: Annotated[str, Field(default="<str:Subscriber ID>")]
    jti: Annotated[str, Field(default="<str:Unique ID>")]

# Ref: https://www.oag.com/hubfs/Inbound-Services/OAG-ACARS-OOOI-Message-Types-and-Examples.pdf
OOOI_SMI_TYPES = {
    "AEP": "POSITION REPORT WITH WEATHER INFORMATION",
    "AGM": "MISCELLANEOUS AG MESSAGE",
    "ALR": "ALERT MESSAGE",
    "ARR": "ARRIVAL REPORT",
    "DEP": "DEPARTURE REPORT",
    "DLA": "FLIGHT DELAY",
    "ETA": "ESTIMATED TIME OF ARRIVAL",
    "GVR": "GROUND ORIGINATED VOICE REQUEST",
    "POS": "POSITION REPORT WITHOUT WEATHER INFORMATION"
}

# https://www.caa.co.uk/media/2cdpufa4/gold_2edition.pdf (Appendix A)
# Ground System > Aircraft System > CPDLC Message Set
GROUND_AND_AIRCRAFT_SYSTEMS:Dict[str, Dict[str, str|None]] = {
    "FANS_1_A": {
        "FANS_1_A": "FANS_1_A",
        "FANS_1_A-A_ATN_B1": "FANS_1_A",
        "ATN_B1": None
    },
    "ATN_B1": {
        "FANS_1_A": None,
        "FANS_1_A-A_ATN_B1": "ATN_B1",
        "ATN_B1": "ATN_B1"
    },
    "FANS_1_A-A_ATN_B1": {
        "FANS_1_A": "FANS_1_A-A_ATN_B1",
        "FANS_1_A-A_ATN_B1": "FANS_1_A-A_ATN_B1",
        "ATN_B1": "ATN_B1"
    },
}

# https://www.caa.co.uk/media/2cdpufa4/gold_2edition.pdf (Appendix A)
CPDLC_UPLINK_MESSAGE_RESPONSES = {
    "W_U": {
        "response_required": True,
        "valid_responses": [
            ("DM0", "WILCO"),
            ("DM1", "UNABLE"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM227", "LOGICAL ACKNOWLEDGEMENT"),
            ("UM159", "ERROR")
        ],
        "will_close_uplink": [
            ("DM0", "WILCO"),
            ("DM1", "UNABLE"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ],
        "FANS_1_A": [
            ("DM0", "WILCO"),
            ("DM1", "UNABLE"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ]
    },
    "A_N": {
        "response_required": True,
        "valid_responses": [
            ("DM4", "AFFIRM"),
            ("DM5", "NEGATIVE"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM227", "LOGICAL ACKNOWLEDGEMENT"),
            ("UM159", "ERROR")
        ],
        "will_close_uplink": [
            ("DM4", "AFFIRM"),
            ("DM5", "NEGATIVE"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ],
        "FANS_1_A": [
            ("DM4", "AFFIRM"),
            ("DM5", "NEGATIVE"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ]
    },
    "R": {
        "response_required": True,
        "valid_responses": [
            ("DM3", "ROGER"),
            ("DM1", "UNABLE"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM227", "LOGICAL ACKNOWLEDGEMENT"),
            ("UM159", "ERROR")
        ],
        "will_close_uplink": [
            ("DM3", "ROGER"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ],
        # FANS 1/A aircraft do not have the capability to send UNABLE in
        # response to an uplink message containing message elements with
        # an “R” response attribute
        "FANS_1_A": [
            ("DM3", "ROGER"),
            ("DM2", "STANDBY"),
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("UM159", "ERROR")
        ]
    },
    "Y": {
        "response_required": True,
        "valid_responses": ["~ANY"],
        "will_close_uplink": [],
        "FANS_1_A": ["~ANY"]
    },
    "N": {
        "response_required": False,
        "valid_responses": [
            ("DM63", "NOT CURRENT DATA AUTHORITY"),
            ("DM107", "NOT AUTHORIZED NEXT DATA AUTHORITY"),
            ("UM227", "LOGICAL ACKNOWLEDGEMENT"),
            ("UM159", "ERROR")
        ],
        "will_close_uplink": [("UM159", "ERROR")],
        "FANS_1_A": ["~NOT USED"]
    },
    "NE": {
        "response_required": False,
        "valid_responses": [], # Not defined in ICAO Doc 4444
        "will_close_uplink": ["~ANY"],
        # FANS 1/A The WILCO, UNABLE, AFFIRM, NEGATIVE, ROGER, and STANDBY
        # responses are not enabled (NE) for flight crew selection.
        "FANS_1_A": []
    }
}

CPDLC_DOWNLINK_MESSAGE_RESPONSES = {
    "Y": {
        "response_required": True,
        "valid_responses": ["~ANY"],
        "will_close_uplink": [],
        "FANS_1_A": ["~ANY"]
    },
    "N": {
        "response_required": False,
        "valid_responses": [
            ("UM162", "SERVICE UNAVAILABLE"),
            ("UM234", "FLIGHT PLAN NOT HELD"),
            ("UM227", "LOGICAL ACKNOWLEDGEMENT"),
            ("UM159", "ERROR")
        ],
        "will_close_uplink": [("UM159", "ERROR")],
        # FANS 1/A.— Aircraft do not have the capability to receive technical
        # responses to downlink message elements with an “N” response attribute
        # (other than LACK or ERROR for ATN B1 aircraft)
        "FANS_1_A": ["~NOT USED"]
    },
}

# Ref: https://www.hoppie.nl/acars/system/tech.html
MSG_TYPES = [
    "progress",
    "cpdlc",
    "telex",
    "adexp",
    "ping",
    "posreq",
    "position",
    "datareq",
    "poll",
    "peek",
    "inforeq",
    "ads-c"
]

NETWORKS = [
    "vatsim",
    "ivao",
    "pilotedge",
    "poscon",
    "apoc",
    "sayintentions",
    "offline",
    "testing"
]

COMMON_ERRORS:dict[int|str,dict[str,Any]]|None = {
    401: {"description": "Unauthorised API Key Provided"},
    403: {"description": "Forbidden by Third Party Provider"}
}

METADATA_TAGS:list[dict[str, Any]] = [
    {
        "name": "Status",
        "description": "System status",
    },
    {
        "name": "User Management",
        "description": "User management",
    },
    {
        "name": "Callbacks",
        "description": "These are callback endpoints for third party OAuth2 services",
    },
    {
        "name": "Messaging",
        "description": "All things non-legacy messaging"
    },
    {
        "name": "Legacy Messaging",
        "description": ("Provides backwards compatability for "
                        "clients configured to work with Hoppie's ACARS"),
        "externalDocs": {
            "description": "Hoppie's ACARS Server API",
            "url": "https://www.hoppie.nl/acars/system/tech.html",
        },
    },
    {
        "name": "Testing",
        "description": "Test bits, you need a DEV API code to do anything here"
    },
    {
        "name": "Data Link Initiation and Capability",
        "description": ("Endpoints related to the Data Link Initiation and "
                        "Capability (DLIC) process as defined in ICAO Doc 4444")
    }
]

# Per https://vats.im/coc-companion [2026-06-19]
PERMANENTLY_BLOCKED_CALLSIGNS = [
    r"^VATSIM\d+$",
    r"^VATGOV\d+$",
    r"^VAT[A-Z]{3}\d+$",
    r"^.*_SUP$",
    r"^.*_ADM$",
    r"^AAL11.*$",
    r"^AAL77.*$",
    r"^MAS17.*$",
    r"^MAS370.*$",
    r"^UAL93.*$",
    r"^UAL175.*$",
]
