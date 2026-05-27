"""
ACARS Server
Virtual Aviation Network Functions
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Union

# Third Party Libraries
import requests

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
        response = requests.get(
            self.SLURPER_URL, params={"cid": cid},
            timeout=30)
        r_data = response.text.split(",")
        if r_data[0] == cid and r_data[1] == callsign:
            return True
        return False

    def get_callsign_from_cid(self, cid:str) -> Union[str, None]:
        """
        Attempts to match the callsign with the CID
        Returns TRUE if slurper callsign matches provided callsign
        """
        response = requests.get(
            self.SLURPER_URL, params={"cid": cid},
            timeout=30)
        r_data = response.text.split(",")
        if len(r_data) > 0:
            return r_data[1]
        return None
