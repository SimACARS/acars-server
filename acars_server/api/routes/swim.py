"""
ACARS Server
System Wide Information Management (SWIM) Endpoints
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Annotated, Literal, Optional

# Third Party Libraries
from fastapi import APIRouter, Query

# Local Libraries

router = APIRouter()

@router.post("/demand-contracts")
async def swim_demand_contracts():
    """
    SWIM Demand Contracts
    in: demandContractRequest
    out: demandContractReply
    error:
        conflictReply
        tooManyRequestsReply
        badRequestReply
        notFoundReply
    """

@router.post("/serviceStatus")
async def swim_service_status():
    """
    SWIM Service Status
    in: 
    out: serviceStatus
    error:
    """

@router.post("/flightStatusSubscriptions")
async def swim_flight_subscribe():
    """
    SWIM Subscribe
    in: 
    out:
    error:
    """

@router.delete("/flightStatusSubscriptions/{sub_id}")
async def swim_flight_unsubscribe(sub_id):
    """
    SWIM Unsubscribe
    in: 
    out:
    error:
    """

@router.get("/flightStatusSubscriptions")
async def swim_flight_list_subscriptions():
    """
    SWIM List Subscriptions
    in: 
    out:
    error:
    """

@router.get("/flightStatusSubscriptions/{sub_id}")
async def swim_flight_list_subscription_details(sub_id):
    """
    SWIM List Subscription Details
    in: 
    out:
    error:
    """

@router.get("/aircraft")
async def swim_aircraft_icao_address(
    flight_id: Annotated[str, Query(alias="flightId", pattern=r"[A-Z0-9]+")],
    adep: Annotated[Optional[str], Query(alias="adep", pattern=r"[A-Z]{4}")],
    ades: Annotated[Optional[str], Query(alias="ades", pattern=r"[A-Z]{4}")],
    ):
    """
    SWIM Get ICAO Aircraft Address
    in: getAircraftAddressRequest
    out: getAircraftAddressReply
    error:
    """

@router.post("/aircraft/{aircraft_id}/{command}")
async def swim_get_aircraft_data(
    aircraft_id: str,
    command: Literal[
        "status",
        "last-report",
        "last-demand-report",
        "last-event-report",
        "last-periodic-report",
        "contract-settings"
        ]
    ):
    """
    SWIM Aircraft Data
    in: 
    out: serviceStatus
    error:
    """

@router.post("/subscriptions")
async def swim_subscribe():
    """
    SWIM Subscribe
    in: 
    out:
    error:
    """

@router.delete("/subscriptions/{sub_id}")
async def swim_unsubscribe(sub_id):
    """
    SWIM Unsubscribe
    in: 
    out:
    error:
    """

@router.get("/subscriptions")
async def swim_list_subscriptions():
    """
    SWIM List Subscriptions
    in: 
    out:
    error:
    """

@router.get("/subscriptions/{sub_id}")
async def swim_list_subscription_details(sub_id):
    """
    SWIM List Subscription Details
    in: 
    out:
    error:
    """
