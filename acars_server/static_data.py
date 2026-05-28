"""
ACARS Server
Static Data Types
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

from typing import Any


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


# Ref: https://www.hoppie.nl/acars/system/tech.html
LEGACY_MSG_TYPES = [
    "progress",
    "cpdlc",
    "telex",
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
    "offline"
]

COMMON_ERRORS:dict[int|str,dict[str,Any]]|None = {
    401: {"description": "Unauthorised API Key Provided"},
    403: {"description": "Forbidden by Third Party Provider"}
}

METADATA_TAGS:list[dict[str, Any]] = [
    {
        "name": "status",
        "description": "System status",
    },
    {
        "name": "user management",
        "description": "User management",
    },
    {
        "name": "callbacks",
        "description": "These are callback endpoints for third party OAuth2 services",
    },
    {
        "name": "messaging",
        "description": "All things non-legacy messaging"
    },
    {
        "name": "legacy messaging",
        "description": "Provides backwards compatability for clients configured to work with Hoppie's ACARS",
        "externalDocs": {
            "description": "Hoppie's ACARS Server API",
            "url": "https://www.hoppie.nl/acars/system/tech.html",
        },
    },
    {
        "name": "testing",
        "description": "Test bits, you need a DEV API code to do anything here"
    },
]
