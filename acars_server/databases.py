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
from pydantic import AfterValidator, SerializeAsAny
from redis_om import get_redis_connection, Field as RedisField, HashModel, JsonModel
from sqlmodel import Column, Field, Relationship, Session, SQLModel, Text, create_engine

# Local Libraries
from acars_server import static_data

load_dotenv()

DATABASE_HOST = os.getenv("MYSQL_HOST", "localhost")
DATABASE_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DATABASE_NAME = os.getenv("MYSQL_DB", "acars")
DATABASE_USER = os.getenv("MYSQL_USER", "acars")
DATABASE_PASSWORD = os.getenv("MYSQL_PASSWORD")

DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

redis_db = get_redis_connection(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    username="default",
    decode_responses=True
)

redis_async_db = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    username="default",
    decode_responses=True
)

# ------------- DEV CODE -------------
redis_db.flushall() # Clear Redis DB on startup
# ------------- DEV CODE -------------

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def create_db_and_tables(): # pragma: no cover
    """Create DB and Tables"""
    SQLModel.metadata.create_all(engine)

def get_session(): # pragma: no cover
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
    domain.encode("idna")
    return domain

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
# CPDLC Message Types
# ------------------------------------------------------------------
class CPDLCTypes(SQLModel, table=True):
    """A table to hold all CPDLC message types"""
    direction: str
    reference_number: Annotated[
        str, Query(
            min_length=3,
            max_length=7,
            pattern="^[UD]M[0-9]{1,3}[a-z]{0,2}$")] = Field(index=True, primary_key=True)
    message_intent: str = Field(sa_column=Column(Text))
    message_element: str
    response_type: str
    fans_1_a: bool = False
    fans_1_a_atn_b1: bool = False
    atn_b1: bool = False

# ------------------------------------------------------------------
# Airline API Keys - For airlines to access the API
# ------------------------------------------------------------------
class AirlineApiKeyBase(SQLModel):
    """A table to hold all API keys"""
    network: Annotated[str, AfterValidator(check_valid_network)]
    airline_name: str
    airline_callsign: Annotated[
        str, Query(min_length=8, max_length=9, pattern="^_COY_[A-Z]+$")]
    domain: Annotated[str, AfterValidator(check_valid_domain)] | None = None


class AirlineApiKey(AirlineApiKeyBase, table=True):
    """A table to hold all API keys"""
    id: int | None = Field(default=None, primary_key=True)
    api_key: str | None = Field(index=True)
    verified: Optional[bool] = False
    created: float
    last_used: float


class AirlineApiKeyCreate(AirlineApiKeyBase):
    """A table to hold all API keys"""
    api_key: str
    verified: bool = False
    created: float
    last_used: float


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
# ATSU Authorised Callsigns
# ------------------------------------------------------------------
class ATSUCallsignOwner(SQLModel, table=True):
    """
    Owner of one or more ATSU callsigns.
    """
    id: int | None = Field(default=None, primary_key=True)
    network: Annotated[str, AfterValidator(check_valid_network)]
    owner: str = Field(index=True)
    api_key: str | None = Field(default=None, index=True)
    created: float
    last_used: float
    atsu_callsigns: list["ATSUCallsign"] = Relationship(
        back_populates="owner"
    )
    authorised_callsigns: list["ATSUAuthorisedCallsign"] = Relationship(
        back_populates="owner"
    )


class ATSUCallsign(SQLModel, table=True):
    """
    ATSU callsign such as _ATC_EGKK or _ATC_LONS.
    """
    id: int | None = Field(default=None, primary_key=True)
    network: Annotated[str, AfterValidator(check_valid_network)]
    atsu_callsign: str = Field(
        index=True,
        min_length=9,
        max_length=9,
        regex=r"^_ATC_[A-Z]+$",
    )
    owner_id: int = Field(
        foreign_key="atsucallsignowner.id",
        index=True,
    )
    owner: ATSUCallsignOwner = Relationship(
        back_populates="atsu_callsigns"
    )
    authorised_callsigns: list["ATSUAuthorisedCallsign"] = Relationship(
        back_populates="atsu_callsign"
    )
    created: float
    last_used: float


class ATSUAuthorisedCallsign(SQLModel, table=True):
    """
    Network callsigns authorised to use an ATSU callsign.
    """
    id: int | None = Field(default=None, primary_key=True)
    network: Annotated[str, AfterValidator(check_valid_network)]
    callsign: str = Field(index=True)
    owner_id: int = Field(
        foreign_key="atsucallsignowner.id",
        index=True,
    )
    atsu_callsign_id: int = Field(
        foreign_key="atsucallsign.id",
        index=True,
    )
    owner: ATSUCallsignOwner = Relationship(
        back_populates="authorised_callsigns"
    )
    atsu_callsign: ATSUCallsign = Relationship(
        back_populates="authorised_callsigns"
    )
    created: float
    last_used: float

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
    primary_frequency: Annotated[
        Optional[str],
        Query(pattern="1[0-3]\\d\\.\\d{3}")] = RedisField(index=True, default=None)

    def __getitem__(self, key):
        return getattr(self, key)

    class Meta:
        """MetaData"""
        database = redis_db


class LogoffRequest(HashModel):
    """A DLIC logoff request"""
    logoff_code: Annotated[
        str, Query(min_length=64, max_length=64, pattern="[a-f0-9]+")]


class OAuthStateStore(HashModel, index=True): # type: ignore
    """A store for OAuth states"""
    oauth_state: Annotated[
        str, Query(
            min_length=64,
            max_length=64,
            pattern="[a-f0-9]+")] = RedisField(index=True, schema_type="tag")

    class Meta:
        """MetaData"""
        database = redis_db


class CpdlcConnectionStateStore(HashModel, index=True): # type: ignore
    """A store for CPDLC connection states states"""
    transaction_str: str = RedisField(index=True)
    expected_next_tx_id: int = 1

    class Meta:
        """MetaData"""
        database = redis_db


class RequestNewAirline(HashModel):
    """A DLIC logoff request"""
    network: Annotated[str, AfterValidator(check_valid_network)]
    airline_callsign: Annotated[
        str, Query(
            min_length=3,
            max_length=4,
            pattern="[A-Z0-9]+")]
    airline_name: str
    domain: Annotated[str, AfterValidator(check_valid_domain)]


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
            max_length=500,
            pattern=r"[A-Z0-9\s\(\)\-\?\:\.\,\'\=\+\/\n\r]+")] = RedisField(
                index=True, full_text_search=True)
    network: Annotated[str, AfterValidator(check_valid_network)] = RedisField(index=True)
    created: float
    relayed: Optional[SerializeAsAny[bool]] = RedisField(index=True, default=False)
    relayed_at: Optional[float] = 0.0

    def __getitem__(self, key):
        return getattr(self, key)

    class Meta:
        """MetaData"""
        database = redis_db
