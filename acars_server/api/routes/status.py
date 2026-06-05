"""
ACARS Server
APP Server Status
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

# Local Libraries
from acars_server import __VERSION__, common

router = APIRouter()
# ------------------------------------------------------------------
# Server Status
# ------------------------------------------------------------------
@router.get("/", tags=["Status"])
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return {"server_status": "OK", "server_version": __VERSION__}

@router.get("/logs/stream", tags=["Status"])
async def stream_logs(): # pragma: no cover
    """Log Streamer"""
    async def event_generator():
        while True:
            # Get item from the queue
            item = await common.stream.get()

            yield {
                "event": "log",
                "data": item
            }

            # Compete the processing
            common.stream.task_done()

    return EventSourceResponse(event_generator())
