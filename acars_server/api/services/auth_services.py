"""
ACARS Server
Authentication Services
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from uuid import uuid4

# Third Party Libraries
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
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


class JWTAuth:
    """JWT Authentication Class"""
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
    strict_jwt = jwt.PyJWT(options={"enforce_minimum_key_length": True})

    @staticmethod
    def token_response(token: str):
        """Returns a JWT token"""
        return {
            "access_token": token,
            "token_type": "bearer"
        }

    async def sign_jwt(
            self,
            network: str,
            uid: str,
            logoff_code: str,
            audience:List[str]) -> Dict[str, str]:
        """Signs a JWT"""
        now = datetime.now(tz=timezone.utc)
        expiry = now + timedelta(hours=3)

        payload = {
            "exp": expiry,
            "nbf": now,
            "iat": now,
            "iss": "urn:simacars",
            "aud": audience,
            "network": network,
            "loc": logoff_code,
            "uid": uid,
            "sub": f"{network}:{uid}",
            "jti": str(uuid4())
        }
        token = jwt.encode(payload, str(self.JWT_SECRET), algorithm=self.JWT_ALGORITHM)

        return self.token_response(token)

    async def decode_jwt(
            self,
            token:HTTPAuthorizationCredentials,
            audience:List[str]) -> Dict[str, str]:
        """Decode a JWT"""
        try:
            decoded_token = jwt.decode(
                jwt=token.credentials,
                key=str(self.JWT_SECRET),
                audience=audience,
                options={
                    "require": [
                        "exp",
                        "nbf",
                        "iat",
                        "iss",
                        "aud",
                        "network",
                        "loc",
                        "uid",
                        "sub",
                        "jti"
                    ]
                    },
                algorithm=self.JWT_ALGORITHM
                )
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(status_code=401, detail="JWT expired signature") from err
        except jwt.InvalidAudienceError as err:
            raise HTTPException(status_code=401, detail="JWT invalid audience") from err
        except jwt.MissingRequiredClaimError as err:
            raise HTTPException(status_code=401, detail="JWT missing claim") from err
        return decoded_token

jwt_auth = JWTAuth()
