"""
ACARS Server
Callbacks
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis_om.model.model import NotFoundError # type: ignore

# Local Libraries
from acars_server import auth, databases
from acars_server.api.services.auth_services import get_api_key_hash

router = APIRouter()
# ------------------------------------------------------------------
# Callback Endpoints
# ------------------------------------------------------------------
@router.get(
        "/oauth/vatsim/aircraft/{state}/{code}",
        response_model=databases.ApiKeyPublic,
        tags=["Callbacks", "User Management"])
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
