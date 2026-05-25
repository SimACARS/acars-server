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
    "peek"
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
    401: {"description": "Unauthorised"},
}
