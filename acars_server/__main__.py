"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from contextlib import asynccontextmanager
from pathlib import Path
from time import sleep

# Third Party Libraries
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from redis_om import Migrator # type: ignore

# Local Libraries
from acars_server import __VERSION__, auth, common, config, databases, static_data
from acars_server.api.routes import acars, airlines, dlic, status, tests, users

load_dotenv()
settings = config.Settings()

def run_startup_tasks():
    """Startup Tasks"""
    databases.create_db_and_tables()
    Migrator().run()

    # Check that a master key exists, if not then create one
    if not Path(common.MASTER_KEY).exists():
        auth.generate_master_key()
        sleep(1)
    if not Path(common.AUTH_KEY).exists():
        auth.generate_auth_key()
        sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """async Context Manager"""
    # ------------------------------------------------------------------
    # Pre App Start
    # ------------------------------------------------------------------
    if not settings.testing:
        run_startup_tasks()

    # ------------------------------------------------------------------
    # App Start
    # ------------------------------------------------------------------
    yield

    # ------------------------------------------------------------------
    # Post App Finish
    # ------------------------------------------------------------------
    config.otel.shutdown()

app = FastAPI(
    lifespan=lifespan,
    title="SimACARS",
    description=(
        "This is a simulated ACARS network for flight simulation only.<br /><br />"
        "If you are flying on a network, your API key is an encrypted string of "
        "SECRET:NETWORK:USER_ID. Your network user ID is used to verify that the "
        "callsign you have logged on with.<br /><br />Your user ID is verified "
        "using your network's OAuth2 protocol. We ONLY store your encrypted user "
        "ID and no other personal data."),
    version=__VERSION__,
    contact={
        "name": "@chssn",
    },
    openapi_tags=static_data.METADATA_TAGS
)
FastAPIInstrumentor.instrument_app(app)
# Serve some static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(common.PWD.parent, "front_end")),
    name="static")

# Server Status Endpoints
app.include_router(status.router)
# User Endpoints
app.include_router(users.router)
# Airline Endpoints
app.include_router(airlines.router, prefix="/airline", tags=["Airline Management"])
# Test Endpoints
app.include_router(tests.router, prefix="/test", tags=["Testing"])
# DLIC (Data Link Initiation and Capability) Endpoints
app.include_router(dlic.router, prefix="/dlic", tags=["Data Link Initiation and Capability"])
# ACARS Endpoints
app.include_router(acars.router, prefix="/acars", tags=["Messaging"])
