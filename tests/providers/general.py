"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from pathlib import Path

# Third Party Libraries
from faker.providers import BaseProvider

# Local Libraries


PWD = Path(os.path.dirname(__file__))

def load_airline_tsv(path: str):
    """Load the airline TSV file"""
    data = []

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()

            # skip separators / junk lines
            if not line or line.startswith(";"):
                continue

            parts = line.split(",")

            # safety check
            if len(parts) < 4:
                continue

            icao, name, callsign, country = parts[:4]

            data.append({
                "icao": icao,
                "name": name,
                "callsign": callsign,
                "country": country
            })

    return data


class AirlineProvider(BaseProvider):
    """Faker provider for airlines"""
    def __init__(self, generator):
        super().__init__(generator)
        self.airlines = load_airline_tsv(
            os.path.join(PWD, "ICAO_Airlines_Clean.txt")
        )

    def _choice(self):
        return self.random_element(self.airlines)

    def airline(self):
        return self._choice()

    def airline_name(self):
        return self._choice()["name"]

    def airline_icao(self):
        return self._choice()["icao"]

    def airline_callsign(self):
        return self._choice()["callsign"]

    def airline_country(self):
        return self._choice()["country"]

    def full_callsign(self):
        airline = self._choice()
        suffix = self.generator.bothify("####")
        return f"{airline['icao']}{suffix}"


class MessageProvider(BaseProvider):
    """Faker provider for messages"""

    def __init__(self, generator):
        super().__init__(generator)
        messages = [
            {"msg_type": "telex", "network": "vatsim", "packet": "TEST1"},
            {"msg_type": "cpdlc", "network": "vatsim", "packet": "/data2/1/1/N/TEST1"}
        ]
        self.msg = self.random_element(messages)

    def message_from_atc(self):
        suffix = self.generator.bothify("????")
        return f"_ATC_{suffix}".upper()

    def message_from_airline(self):
        suffix = self.generator.bothify("???")
        return f"_COY_{suffix}".upper()

    def message_type(self):
        return self.msg["msg_type"]

    def message_network(self):
        return self.msg["network"]

    def message_packet(self):
        return self.msg["packet"]


class NetworkProvider(BaseProvider):
    """Faker provider for networks"""
    def network(self):
        """Return a random network"""
        #return self.random_element(static_data.NETWORKS)
        return "vatsim"


class DomainProvider(BaseProvider):
    """Faker provider for networks"""
    def domain(self):
        """Return a random network"""
        return "test.com"


class NetworkCidProvider(BaseProvider):
    """Faker provider for network cids"""
    def network_cid(self):
        """Return a random network cid"""
        return self.generator.bothify("########")
