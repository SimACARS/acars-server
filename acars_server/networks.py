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
from acars_server import common


class Vatsim:
    """Something to do with Vatsim stations"""

    SLURPER_URL = "https://slurper.vatsim.net/users/info"

    def __init__(self) -> None:
        pass

    def get_callsign_from_cid(self, cid:str) -> Union[str, None]:
        """
        Attempts to match the callsign with the CID
        Returns TRUE if slurper callsign matches provided callsign
        """
        response = requests.get(
            self.SLURPER_URL, params={"cid": cid},
            timeout=30)
        if response.status_code == 200:
            r_data = response.text.split(",")
            common.logger.debug(f"{response.text}")
            if len(r_data) > 1:
                return r_data[1]
        else:
            common.logger.warning(f"{response.url} returned {response.status_code}")
        return None
