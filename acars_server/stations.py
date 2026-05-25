"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import base64
import os
import secrets
import string
from typing import Dict, Tuple

# Third Party Libraries
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from loguru import logger

# Local Libraries


class Vatsim:
    """Something to do with Vatsim stations"""

    SLURPER_URL = "https://slurper.vatsim.net/users/info"

    def __init__(self) -> None:
        pass

    def corrolate_cid_to_callsign(self, cid:str, callsign:str) -> bool:
        """
        Attempts to match the callsign with the CID
        Returns TRUE if slurper callsign matches provided callsign
        """
        response = requests.get(self.SLURPER_URL, params={"cid": cid})
        r_data = response.text.split(",")
        if r_data[0] == cid and r_data[1] == callsign:
            return True
        return False
