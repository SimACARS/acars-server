"""
ACARS Server
Authentication Services
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Dict

# Third Party Libraries
from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlmodel import select

# Local Libraries
from acars_server import auth, common, databases, static_data, networks

password_hash = PasswordHash.recommended()

def get_api_key_hash(api_key: str) -> str:
    """Returns a hash of the given API key"""
    return password_hash.hash(api_key)

async def api_authentication(session:databases.SessionDep, api_key:str) -> Dict[str,str]:
    """Authenticates an API Key"""
    hashed_api = get_api_key_hash(api_key)

    db_auth = select(databases.ApiKey).where(databases.ApiKey.api_key == hashed_api)
    api_user = session.exec(db_auth).first()
    if not api_user:
        common.logger.error("401: API key not recognised. This is an AIRCRAFT endpoint.")
        raise HTTPException(status_code=401, detail="Unauthorised. This is an AIRCRAFT endpoint.")
    return auth.Auth().api_key_reader(api_key)

async def airline_api_authentication(
        session:databases.SessionDep, api_key:str) -> databases.AirlineApiKey:
    """Authenticates an API Key"""
    hashed_api = get_api_key_hash(api_key)

    db_auth = select(databases.AirlineApiKey).where(databases.AirlineApiKey.api_key == hashed_api)
    api_airline = session.exec(db_auth).first()
    if not api_airline:
        common.logger.error("401: API key not recognised. This is an AIRLINE endpoint.")
        raise HTTPException(status_code=401, detail="Unauthorised. This is an AIRLINE endpoint.")
    return api_airline

async def callsign_verification(user_data) -> str|None:
    """Validate callsign on various networks"""
    callsign = None
    if user_data["network"] == "vatsim":
        vc = networks.Vatsim()
        callsign = vc.get_callsign_from_cid(user_data["uid"])
    elif user_data["network"] == "testing":
        return "TEST1"
    else:
        common.logger.error(f"400: Network '{user_data['network']}' is not valid. "
                    f"Expected one of {', '.join(static_data.NETWORKS)}")
        raise HTTPException(
            status_code=400,
            detail=(f"Network '{user_data['network']}' is not valid. "
                    f"Expected one of {', '.join(static_data.NETWORKS)}"))
    return callsign
