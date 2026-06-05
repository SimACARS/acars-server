"""
ACARS Server
User Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse

# Local Libraries
from acars_server import auth, common, databases, static_data
from acars_server.api.services.user_services import responses_user_new_network

router = APIRouter()
# ------------------------------------------------------------------
# User Endpoints
# ------------------------------------------------------------------
@router.get("/user/new/{network}", tags=["User Management"], responses=responses_user_new_network)
async def auth_new_user(network: str):
    """Authenticate a new user and generate an API key"""
    if network in static_data.NETWORKS:
        if network == "vatsim":
            v_auth = auth.VatsimAuth()
            v_url = v_auth.authorise()
            common.logger.success("Client redirected to VATSIM OAuth")
            return RedirectResponse(v_url[0])

        error = f"{network} doesn't appear to exist although it really should..."
        common.logger.error(error)
        return JSONResponse(status_code=400, content={"error": error})

    error = (f"{network} is not a recognised network. Needs to be one of "
             f"{', '.join(static_data.NETWORKS)}")
    common.logger.error(error)
    return JSONResponse(status_code=400, content={"error": error})

@router.get(
        "/callback/oauth/vatsim/{state}/{code}",
        response_model=databases.ApiKeyPublic,
        tags=["Callbacks"])
async def auth_new_user_callback_vatsim(
    state:str,
    code:str,
    session: databases.SessionDep
    ):
    """A callback point for VATSIM"""
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

    # Add the API key to the DB
    dtnow = dt.now(tz.utc).timestamp()
    db_data = {
        "api_key": api_key,
        "network": "vatsim",
        "created": dtnow,
        "last_used": dtnow
    }
    db_add = databases.ApiKey.model_validate(db_data)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return JSONResponse({"status": "user created", "api_key": db_add.api_key})
