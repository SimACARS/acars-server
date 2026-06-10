"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import secrets
from typing import Tuple

# Third Party Libraries

# Local Libraries
from acars_server.auth import Auth
from acars_server.api.services.auth_services import get_api_key_hash
from acars_server.databases import AirlineApiKey
from tests.factories.airlines import AirlineApiKeyFactory

auth = Auth()

def create_airline_api_key() -> Tuple[AirlineApiKey,str]:
    """Create an API key"""
    raw_key = secrets.token_hex(64)

    api_key: AirlineApiKey = AirlineApiKeyFactory(
        api_key=get_api_key_hash(raw_key)
    )

    return api_key, raw_key
