"""
ACARS Server
User Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

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
@router.get("/user/new/{network}", tags=["User Management"], status_code=307)
async def auth_new_user(network: str):
    """Authenticate a new user and generate an API key"""
    if network in static_data.NETWORKS:
        if network == "vatsim":
            v_auth = auth.VatsimAuth()
            v_url = v_auth.authorise()

            # Add state key to redis
            state_model = {
                "oauth_state": v_url[1]
            }
            state_key = databases.OAuthStateStore.model_validate(state_model)

            # Expire state key in 10 minutes
            state_key.save()
            databases.redis_db.expire(
                state_key.key(),
                600,
            )

            common.logger.success("Client redirected to VATSIM OAuth")
            return RedirectResponse(v_url[0])

        error = f"{network} doesn't appear to exist although it really should..."
        common.logger.error(error)
        return JSONResponse(status_code=400, content={"error": error})

    error = (f"{network} is not a recognised network. Needs to be one of "
             f"{', '.join(static_data.NETWORKS)}")
    common.logger.error(error)
    return JSONResponse(status_code=400, content={"error": error})
