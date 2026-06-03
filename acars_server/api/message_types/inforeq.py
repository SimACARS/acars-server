"""
ACARS Server
INFOREQ Message Responses
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
import pandas as pd # type: ignore
import requests

# Local Libraries
from acars_server import common, functions


class Noaa:
    """Class for various NOAA functions"""
    BASE_URL = "https://tgftp.nws.noaa.gov/data/"

    def __init__(self) -> None:
        pass # pragma: no cover

    @staticmethod
    def metar(icao:str) -> str:
        """Gets a METAR from NOAA"""
        try:
            rsp = requests.get(
                f"{Noaa.BASE_URL}/observations/metar/stations/{icao.upper()}.TXT",
                timeout=30)
            if rsp.status_code == 200:
                return rsp.text
        except requests.ReadTimeout:
            common.logger.error(f"Timeout while fetching METAR for {icao.upper()}")
        return f"NO METAR AVAILABLE FOR {icao.upper()}"

    @staticmethod
    def taf(icao:str) -> str:
        """Gets a TAF from NOAA"""
        try:
            rsp = requests.get(
            f"{Noaa.BASE_URL}/forecasts/taf/stations/{icao.upper()}.TXT",
            timeout=30)
            if rsp.status_code == 200:
                return rsp.text
        except requests.ReadTimeout:
            common.logger.error(f"Timeout while fetching TAF for {icao.upper()}")
        return f"NO TAF AVAILABLE FOR {icao.upper()}"

    @staticmethod
    def shorttaf(icao:str) -> str:
        """Gets a SHORT TAF from NOAA"""
        try:
            rsp = requests.get(
                f"{Noaa.BASE_URL}/forecasts/shorttaf/stations/{icao.upper()}.TXT",
                timeout=30)
            if rsp.status_code == 200:
                return rsp.text
        except requests.ReadTimeout:
            common.logger.error(f"Timeout while fetching SHORT TAF for {icao.upper()}")
        return f"NO SHORT TAF AVAILABLE FOR {icao.upper()}"


class Vatsim:
    """Class for various live VATSIM functions"""

    def __init__(self):
        # get the most up-to-date URLs from status.vatsim.net
        vatsim_status_url = "https://status.vatsim.net/status.json"

        vatsim_servers = functions.load_json_url(vatsim_status_url, timeout=30)
        common.logger.debug(vatsim_servers)

        self.member_stat_data = {}
        self.msd_rate_limit = functions.RateLimiter(1, 10)

        # json output from status.vatsim.net/status.json is sub-divided by data, user and metar.
        # only data has further sub-divisions.
        vs_data = vatsim_servers["data"]
        self.vatsim_urls = {
            "all": str(vs_data["v3"]).strip("'[]"),
            "transceivers": str(vs_data["transceivers"]).strip("'[]"),
            "primary_servers": str(vs_data["servers"]).strip("'[]"),
            "sweatbox_servers": str(vs_data["servers_sweatbox"]).strip("'[]"),
            "all_servers": str(vs_data["servers_all"]).strip("'[]"),
            "user_details": str(vatsim_servers["user"]).strip("'[]"),
            "metar": str(vatsim_servers["metar"]).strip("'[]"),
            "map_api": "https://api.vatsim.net/api/map_data/",
            "slurper": "https://slurper.vatsim.net/users/info",
            "member_data": "https://api.vatsim.net/v2/members/"
        }
        self.dataframes = {}
        #threading.Thread(target=self._data_collector).start()
        #sleep(1)

    def _data_collector(self) -> None:
        """Collects data from VATSIM 'all' server"""

        r_sections = [
            "atis",
        ]

        response_json = functions.load_json_url(self.vatsim_urls["all"])

        # Put the data into dataframes
        df_update = {}
        for section in r_sections:
            try:
                df_update[section] = pd.json_normalize(response_json, record_path=[section])
            except KeyError as err:
                common.logger.error(f"Unable to find {section} - {err}")
                continue

        self.dataframes = df_update

    def get_atis(self, icao:str) -> str:
        """Get ATIS"""
        self._data_collector()
        df = self.dataframes["atis"]
        dfb = df.loc[df["callsign"].str.match(f"{icao}_ATIS")]
        if not dfb.empty:
            return str(df["text_atis"].iloc[0])

        # If the client has requested an Arrival or Departure ATIS but
        # none is found, check to see if a combined ATIS is available
        remove_a_d =  icao.split("_")
        if len(remove_a_d) == 2:
            dfc = df.loc[df["callsign"].str.match(f"{remove_a_d[0]}_ATIS")]
            if not dfc.empty:
                return str(df["text_atis"].iloc[0])
        return "NO ATIS AVAILABLE"

    @staticmethod
    def get_metar(icao:str) -> str:
        """Get METAR from VATSIM"""
        rsp = requests.get(
            f"https://metar.vatsim.net/{icao.upper()}", timeout=30)
        if rsp.status_code == 200:
            return rsp.text
        return f"NO METAR AVAILABLE FOR {icao.upper()}"
