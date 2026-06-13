"""
ACARS Server
Division Staff ATSU Editor
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi import APIRouter, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlmodel import select

# Local Libraries
from acars_server import common, databases, static_data
from acars_server.api.services.auth_services import jwt_auth

router = APIRouter()

@router.post(
        "/new/atsu_callsign_owner",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.ATSUCallsignOwner
        )
async def add_new_atsu_callsign_owner(
    msg:databases.ATSUCallsignOwner,
    session:databases.SessionDep,
    jwt:HTTPAuthorizationCredentials = Security(common.header_bearer)):
    """
    Add a new ATSU callsign owner
    """

    user_data = await jwt_auth.decode_jwt(jwt, ["admin:atsu:super"])

    db_check = select(databases.ATSUCallsignOwner).where(
            (databases.ATSUCallsignOwner.owner == msg.owner),
            (databases.ATSUCallsignOwner.network == msg.network),)
    db_result = session.exec(db_check).first()

    if db_result:
        return JSONResponse(
            status_code=201,
            content={"error": f"{msg.owner} already exists"})

    db_add = databases.ATSUCallsignOwner.model_validate(msg)
    session.add(db_add)
    session.commit()
    session.refresh(db_add)
    return JSONResponse(content=db_add.model_dump_json())
