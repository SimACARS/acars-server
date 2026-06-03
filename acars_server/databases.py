"""
ACARS Server
SQL Connection and Models
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import re
from typing import Annotated, Optional

# Third Party Libraries
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import Depends, Query
from pydantic import AfterValidator
from redis_om import get_redis_connection, Field as RedisField, HashModel, JsonModel
from sqlmodel import Field, Session, SQLModel, create_engine

# Local Libraries
from acars_server import static_data

load_dotenv()

SQLITE_FILE_NAME = "database.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILE_NAME}"

redis_db = get_redis_connection(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    username="default",
    decode_responses=True
)

redis_async_db = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    username="default",
    decode_responses=True
)

# ------------- DEV CODE -------------
redis_db.flushall(asynchronous=True) # Clear Redis DB on startup
# ------------- DEV CODE -------------

connect_args = {"check_same_thread": False}
engine = create_engine(SQLITE_URL, connect_args=connect_args)

def create_db_and_tables():
    """Create DB and Tables"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Get the Session"""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def check_valid_network(legacy_type: str):
    """Check if the message type is valid"""
    if legacy_type not in static_data.NETWORKS:
        raise ValueError(
            f"Invalid network: Valid networks are: {', '.join(static_data.NETWORKS)}")
    return legacy_type

DOMAIN_RE = re.compile(r"^(?!https?://)[A-Za-z0-9.-]+$")

def check_valid_domain(domain: str):
    """Check if the domain is valid"""
    domain = domain.strip().lower().rstrip(".")
    if not DOMAIN_RE.fullmatch(domain):
        raise ValueError(f"Invalid domain: {domain} is not a valid domain name")
    try:
        domain.encode("idna")
        return domain
    except UnicodeError as err:
        raise ValueError(f"Invalid domain: {domain} is not a valid domain name") from err

# ------------------------------------------------------------------
# API Key Models
# ------------------------------------------------------------------
class ApiKeyBase(SQLModel):
    """A table to hold all API keys"""
    api_key: str | None = Field(index=True)
    network: Annotated[str, AfterValidator(check_valid_network)]


class ApiKey(ApiKeyBase, table=True):
    """A table to hold all API keys"""
    id: int | None = Field(default=None, primary_key=True)
    created: float
    last_used: float


class ApiKeyCreate(ApiKeyBase):
    """A table to hold all API keys"""
    created: float
    last_used: float


class ApiKeyPublic(ApiKeyBase):
    """A table to hold all API keys"""
    api_key: str
    network: str


class ApiKeyUpdate(ApiKeyBase):
    """A table to hold all API keys"""
    api_key: str | None = None
    network: str | None = None
    last_used: float | None = None


# ------------------------------------------------------------------
# Airline API Keys - For airlines to access the API
# ------------------------------------------------------------------
class AirlineApiKeyBase(SQLModel):
    """A table to hold all API keys"""
    network: Annotated[str, AfterValidator(check_valid_network)]
    airline_name: str
    airline_callsign: Annotated[
        str, Query(min_length=3, max_length=4, pattern="^[A-Z]+$")]
    domain: Annotated[str, AfterValidator(check_valid_domain)] | None = None

    def __getitem__(self, key):
        return getattr(self, key)


class AirlineApiKey(AirlineApiKeyBase, table=True):
    """A table to hold all API keys"""
    id: int | None = Field(default=None, primary_key=True)
    api_key: str | None = Field(index=True)
    verified: Optional[bool] = False
    created: float
    last_used: float

    def __getitem__(self, key):
        return getattr(self, key)


class AirlineApiKeyCreate(AirlineApiKeyBase):
    """A table to hold all API keys"""
    api_key: str
    verified: bool = False
    created: float


class AirlineApiKeyPublic(AirlineApiKeyBase):
    """A table to hold all API keys"""
    api_key: str
    network: str
    airline_name: str
    airline_callsign: str
    verified: Optional[bool] = False
    domain: Optional[str] = None


class AirlineApiKeyUpdate(AirlineApiKeyBase):
    """A table to hold all API keys"""
    api_key: str | None = None
    network: str | None = None
    last_used: float | None = None


class AirlineVerification(JsonModel, index=True): # type: ignore
    """Airline Verification for domain ownership"""
    verification_token: str = RedisField(index=True)
    network: Annotated[str, AfterValidator(check_valid_network)] = RedisField(index=True)
    airline_name: str = RedisField(index=True)
    airline_callsign: Annotated[
        str, Query(min_length=3, max_length=4, pattern="^[A-Z]+$")] = RedisField(index=True)
    domain: Annotated[str, AfterValidator(check_valid_domain)] = RedisField(index=True)

    class Meta:
        """MetaData"""
        database = redis_db


# ------------------------------------------------------------------
# Store and Forward Model
# ------------------------------------------------------------------
def check_valid_legacy_msg_type(legacy_type: str):
    """Check if the message type is valid"""
    if legacy_type not in static_data.MSG_TYPES:
        raise ValueError(
            f"Invalid message type: Valid types are: {', '.join(static_data.MSG_TYPES)}")
    return legacy_type


class DataLinkInitiationCapability(HashModel, index=True): # type: ignore
    """A table to hold all the messages"""
    logon_from: Annotated[
        str, Query(
            min_length=3,
            max_length=15,
            pattern="(_COY_|_ATC_)?([A-Z0-9]+)")] = RedisField(index=True)
    logon_to: Annotated[
        str, Query(
            min_length=3,
            max_length=15,
            pattern="(_COY_|_ATC_)?([A-Z0-9]+)")] = RedisField(index=True)
    created: float
    network: Annotated[str, AfterValidator(check_valid_network)] = RedisField(index=True)
    logoff_code: Optional[str] = RedisField(index=True, schema_type="tag")
    fans_1_a_atn_b1: Optional[bool] = False
    atn_b1: Optional[bool] = False
    fans_1_a: Optional[bool] = False

    def __getitem__(self, key):
        return getattr(self, key)

    class Meta:
        """MetaData"""
        database = redis_db


class LogoffRequest(HashModel):
    """A DLIC logoff request"""
    logoff_code: Annotated[
        str, Query(min_length=64, max_length=64, pattern="^[a-f0-9]+$")]
    def __getitem__(self, key):
        return getattr(self, key)


class StoreAndForward(JsonModel, index=True): # type: ignore
    """A table to hold all the messages"""
    msg_from: Annotated[
        str, Query(
            min_length=4,
            max_length=10,
            pattern="(_COY_|_ATC_)?[A-Z0-9]+")] = RedisField(index=True)
    msg_to: Annotated[
        str, Query(
            min_length=4,
            max_length=10,
            pattern="(_COY_|_ATC_)?[A-Z0-9]+")] = RedisField(index=True)
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)] = RedisField(index=True)
    # EUROCONTROL-SPEC-107 - 5.1.1.4 - Allowed Characters
    packet: Annotated[
        str, Query(
            min_length=4,
            max_length=10,
            pattern=r"[A-Z0-9\s\(\)\-\?\:\.\,\'\=\+\/\n\r]+")] = RedisField(
                index=True, full_text_search=True)
    network: Annotated[str, AfterValidator(check_valid_network)] = RedisField(index=True)
    created: float
    relayed: Optional[bool] = RedisField(index=True, default=False)
    relayed_at: Optional[float] = 0.0

    def __getitem__(self, key):
        return getattr(self, key)

    class Meta:
        """MetaData"""
        database = redis_db
