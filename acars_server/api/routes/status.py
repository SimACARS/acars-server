"""
ACARS Server
APP Server Status
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

# Local Libraries
from acars_server import __VERSION__, common

router = APIRouter()
# ------------------------------------------------------------------
# Server Status
# ------------------------------------------------------------------


class ResponseStatus(BaseModel):
    """Status Response"""
    server_status:str="{OK|DEGRADED}"
    server_version: str=__VERSION__

@router.get("/", tags=["Status"], response_model=ResponseStatus)
async def ping():
    """Ping the server. Returns 'OK' and VERSION"""
    return JSONResponse(
        status_code=200,
        content={"server_status": "OK", "server_version": __VERSION__}
        )

EXAMPLE_JS_SOURCE = """const logContainer = document.getElementById("logs");
const eventSource = new EventSource("/logs/stream");

eventSource.addEventListener("log", (event) => {
    logContainer.textContent += event.data + "\n";
    // auto-scroll
    window.scrollTo(0, document.body.scrollHeight);
});

eventSource.onerror = () => {
    console.log("Connection lost...");
};
"""

@router.get(
        "/logs/stream",
        tags=["Status"],
        summary="Log Streamer",
        description="This endpoint shouldn't be called directly. It will print log entries.",
        openapi_extra={
            "x-codeSamples": [
                {
                    "lang": "JavaScript",
                    "source": EXAMPLE_JS_SOURCE
                }
            ]},
        )
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
