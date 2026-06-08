"""
ACARS Server
Callbacks
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from datetime import datetime as dt, timedelta, timezone as tz

# Third Party Libraries
import jwt
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from redis_om.model.model import NotFoundError # type: ignore

# Local Libraries
from acars_server import auth, common, databases
from acars_server.api.services.atsu_services import complete_vatsim_atsu_logon
from acars_server.api.services.auth_services import get_api_key_hash, jwt_auth

router = APIRouter()
# ------------------------------------------------------------------
# Callback Endpoints
# ------------------------------------------------------------------
@router.get(
        "/oauth/vatsim/aircraft/{state}/{code}",
        response_model=databases.ApiKeyPublic,
        tags=["User Management"])
async def auth_new_user_callback_vatsim(
    state:str,
    code:str,
    session: databases.SessionDep
    ):
    """A callback point for VATSIM"""
    # Verify that the state code exists
    try:
        state_code = databases.OAuthStateStore.find(
                    (databases.OAuthStateStore.oauth_state == state)
                ).first()
    except NotFoundError:
        return JSONResponse(status_code=404, content={"error": "State code not found"})
    state_code.delete(state_code.pk)

    # Get the access token from VATSIM
    v_auth = auth.VatsimAuth()
    v_token = v_auth.get_access_token(code)
    if v_token[0] != 200:
        return JSONResponse(
            status_code=v_token[0], content={"error": v_token[1]["hint"]})

    # Get the user details using the access token
    v_user = v_auth.get_user_details(v_token[1]["access_token"])
    if v_user[0] != 200:
        return JSONResponse(status_code=v_user[0], content={"error": v_user[1]})

    # Generate the API key using the cid
    v_cid = v_user[1]["data"]["cid"]
    api_key = auth.Auth().api_key_generator(v_cid, "vatsim")

    # Add the hashed API key to the DB
    dtnow = dt.now(tz.utc).timestamp()
    db_data = {
        "api_key": get_api_key_hash(api_key),
        "network": "vatsim",
        "created": dtnow,
        "last_used": dtnow
    }
    db_add = databases.ApiKey.model_validate(db_data)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return JSONResponse({"status": "user created", "api_key": api_key})

@router.get(
        "/oauth/vatsim/atsu/{state}/{code}",
        response_model=databases.ApiKeyPublic,
        tags=["Air Traffic Surveillance Unit"])
async def atsu_callback_vatsim(state:str, code:str):
    """A callback point for VATSIM"""
    # Verify that the state code exists
    try:
        state_code = databases.OAuthStateStore.find(
                    (databases.OAuthStateStore.oauth_state == state)
                ).first()
    except NotFoundError:
        return JSONResponse(status_code=404, content={"error": "State code not found"})
    state_code.delete(state_code.pk)

    # Get the access token from VATSIM
    v_auth = auth.VatsimAuth(redirect_type="atsu")
    v_token = v_auth.get_access_token(code)
    if v_token[0] != 200:
        return JSONResponse(
            status_code=v_token[0], content={"error": v_token[1]["hint"]})

    # Get the user details using the access token
    v_user = v_auth.get_user_details(v_token[1]["access_token"])
    if v_user[0] != 200:
        return JSONResponse(status_code=v_user[0], content={"error": v_user[1]})

    return await complete_vatsim_atsu_logon(v_user[1]["data"])

@router.post("/atsu/refresh")
async def refresh_atsu_jwt(
    token:HTTPAuthorizationCredentials = Security(common.header_bearer)):
    """
    Call this endpoint to refresh an ATSU JWT

    This endpoint allows leeway on the JWT expiry and will call
    callsign_verification to check if the user is still online
    before issuing an updated JWT
    """

    try:
        decoded_token = jwt.decode(
            jwt=token.credentials,
            key=str(os.getenv("JWT_SECRET")),
            audience=["acars:atsu"],
            issuer="urn:simacars",
            leeway=timedelta(minutes=10),
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
            algorithms=[str(os.getenv("JWT_ALGORITHM"))]
            )
    except jwt.ExpiredSignatureError as err:
        raise HTTPException(status_code=401, detail="JWT expired signature") from err
    except jwt.InvalidAudienceError as err:
        raise HTTPException(status_code=401, detail="JWT invalid audience") from err
    except jwt.MissingRequiredClaimError as err:
        raise HTTPException(status_code=401, detail="JWT missing claim") from err
    except jwt.InvalidSignatureError as err:
        raise HTTPException(status_code=401, detail="JWT invalid signature") from err

    updated_jwt = await jwt_auth.sign_jwt(
        decoded_token["network"],
        decoded_token["uid"],
        decoded_token["logoff"],
        ["acars:atsu"],
        timedelta(minutes=10)
        )
    return JSONResponse(content=updated_jwt)
