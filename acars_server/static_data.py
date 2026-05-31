"""
ACARS Server
Static Data Types
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

from typing import Any, Dict


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
            "WILCO",
            "UNABLE",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "LOGICAL ACKNOWLEDGEMENT",
            "ERROR"
        ],
        "will_close_uplink": [
            "WILCO",
            "UNABLE",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "ERROR"
        ],
        "FANS_1_A": [
            "WILCO",
            "UNABLE",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "ERROR"
        ]
    },
    "A_N": {
        "response_required": True,
        "valid_responses": [
            "AFFIRM",
            "NEGATIVE",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "LOGICAL ACKNOWLEDGEMENT",
            "ERROR"
        ],
        "will_close_uplink": [
            "AFIRM",
            "NEGATIVE",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "ERROR"
        ],
        "FANS_1_A": [
            "AFIRM",
            "NEGATIVE",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "ERROR"
        ]
    },
    "R": {
        "response_required": True,
        "valid_responses": [
            "ROGER",
            "UNABLE",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "LOGICAL ACKNOWLEDGEMENT",
            "ERROR"
        ],
        "will_close_uplink": [
            "ROGER",
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "ERROR"
        ],
        # FANS 1/A aircraft do not have the capability to send UNABLE in
        # response to an uplink message containing message elements with
        # an “R” response attribute
        "FANS_1_A": [
            "ROGER",
            "STANDBY",
            "NOT CURRENT DATA AUTHORITY",
            "ERROR"
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
            "NOT CURRENT DATA AUTHORITY",
            "NOT AUTHORIZED NEXT DATA AUTHORITY",
            "LOGICAL ACKNOWLEDGEMENT",
            "ERROR"
        ],
        "will_close_uplink": ["ERROR"],
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
            "SERVICE UNAVAILABLE",
            "FLIGHT PLAN NOT HELD",
            "LOGICAL ACKNOWLEDGEMENT",
            "ERROR"
        ],
        "will_close_uplink": ["ERROR"],
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
