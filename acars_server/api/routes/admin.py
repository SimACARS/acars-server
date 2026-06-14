"""
ACARS Server
Division Staff ATSU Editor
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import secrets
from typing import Literal

# Third Party Libraries
from fastapi import APIRouter, HTTPException, Security
from fastapi.responses import JSONResponse
from sqlmodel import select

# Local Libraries
from acars_server import common, databases, static_data
from acars_server.api.services.auth_services import admin_api_authentication, get_api_key_hash

router = APIRouter()

@router.post(
        "/{action}/atsu_callsign_owner",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.ATSUCallsignOwner
        )
async def add_new_atsu_callsign_owner(
    action: Literal["add", "delete"],
    msg:databases.ATSUCallsignOwner,
    session:databases.SessionDep,
    api_key:str = Security(common.header_api_key)):
    """
    Add a new ATSU callsign owner
    """

    try:
        await admin_api_authentication(session, api_key)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    if action == "add":
        db_check = select(databases.ATSUCallsignOwner).where(
                (databases.ATSUCallsignOwner.owner == msg.owner),
                (databases.ATSUCallsignOwner.network == msg.network),)
        db_result = session.exec(db_check).first()

        if db_result:
            return JSONResponse(
                status_code=201,
                content={"error": f"{msg.owner} already exists"})

        api_key = secrets.token_hex(64)
        msg.api_key = get_api_key_hash(api_key)
        common.logger.debug(msg.model_dump())

        db_add = databases.ATSUCallsignOwner.model_validate(msg.model_dump())
        session.add(db_add)
        session.commit()

        rtn = {
            "api_key": api_key,
            "response": db_add.model_dump()
        }

        return JSONResponse(content=rtn)
    elif action == "delete":
        raise HTTPException(status_code=501, detail="Delete action not implemented")

@router.post(
        "/{action}/atsu_callsign",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.ATSUCallsign
        )
async def add_new_atsu_callsign(
    action: Literal["add", "delete"],
    msg:databases.ATSUCallsign,
    session:databases.SessionDep,
    api_key:str = Security(common.header_api_key)):
    """
    Add a new ATSU callsign owner
    """

    try:
        api_admin = await admin_api_authentication(session, api_key)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    common.logger.debug(api_admin)

    if action == "add" and api_admin.id is not None:
        db_check = select(databases.ATSUCallsign).where(
                (databases.ATSUCallsign.atsu_callsign == msg.atsu_callsign),
                (databases.ATSUCallsign.network == msg.network),)
        db_result = session.exec(db_check).first()
        common.logger.debug(db_result)

        if db_result:
            return JSONResponse(
                status_code=201,
                content={"error": f"{msg.atsu_callsign} already exists"})

        msg.owner_id = api_admin.id
        common.logger.debug(f"{msg.owner_id} {api_admin.id}")
        common.logger.debug(msg.model_dump())
        db_add = databases.ATSUCallsign.model_validate(msg.model_dump())
        session.add(db_add)
        session.commit()
        return JSONResponse(content=msg.model_dump())
    elif action == "delete":
        ...

@router.post(
        "/{action}/atsu_authorised_callsign/{atsu_callsign}",
        status_code=201,
        responses=static_data.COMMON_ERRORS,
        response_model=databases.ATSUCallsignOwner
        )
async def add_new_authorised_atsu_callsign(
    action: Literal["add", "delete"],
    msg: databases.ATSUAuthorisedCallsign,
    atsu_callsign: str,
    session: databases.SessionDep,
    api_key: str = Security(common.header_api_key)):
    """
    Add a new ATSU callsign owner
    """

    try:
        api_admin = await admin_api_authentication(session, api_key)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    if action == "add" and api_admin.id is not None:
        db_check = select(databases.ATSUAuthorisedCallsign).where(
                (databases.ATSUAuthorisedCallsign.callsign == msg.callsign),
                (databases.ATSUAuthorisedCallsign.network == msg.network),)
        db_result = session.exec(db_check).first()

        if db_result:
            return JSONResponse(
                status_code=201,
                content={"error": f"{msg.callsign} already exists"})

        get_callsign_id = select(databases.ATSUCallsign).where(
                (databases.ATSUCallsign.atsu_callsign == atsu_callsign),
                (databases.ATSUCallsign.network == msg.network),)
        callsign_id_result = session.exec(get_callsign_id).first()

        if callsign_id_result and callsign_id_result.id is not None:
            msg.owner_id = api_admin.id
            msg.atsu_callsign_id = callsign_id_result.id
            db_add = databases.ATSUAuthorisedCallsign.model_validate(msg.model_dump())
            session.add(db_add)
            session.commit()
            return JSONResponse(content=msg.model_dump())
        else:
            return JSONResponse(
                status_code=201,
                content={"error": f"{atsu_callsign} doesn't exist"})
    elif action == "delete":
        ...
