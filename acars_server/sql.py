"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz
from typing import Annotated

# Third Party Libraries
from fastapi import Depends, Query
from pydantic import AfterValidator
from sqlmodel import Field, Session, SQLModel, create_engine

# Local Libraries
from acars_server import static_data


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ------------------------------------------------------------------
# API Key Models
# ------------------------------------------------------------------
class ApiKeyBase(SQLModel):
    """A table to hold all API keys"""
    api_key: str = Field(index=True)
    network: str


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
# Legacy Store and Forward Model
# ------------------------------------------------------------------
def check_valid_legacy_msg_type(legacy_type: str):
    """Check if the message type is valid"""
    if legacy_type not in static_data.LEGACY_MSG_TYPES:
        raise ValueError(f"Invalid message type: Valid types are: {', '.join(static_data.LEGACY_MSG_TYPES)}")
    return legacy_type


class StoreAndForwardBase(SQLModel):
    """A table to hold all the messages"""
    msg_from: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")]
    msg_to: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")]
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)]
    packet: str
    network: str

    def __getitem__(self, key):
        return getattr(self, key)


class StoreAndForward(StoreAndForwardBase, table=True):
    """A table to hold all the messages"""
    id: int | None = Field(default=None, primary_key=True)
    created: float
    relayed: bool
    relayed_at: float


class StoreAndForwardCreate(StoreAndForwardBase):
    """A table to hold all the messages"""
    created: float = dt.now(tz.utc).timestamp()
    relayed: bool = False
    relayed_at: float


class StoreAndForwardPublic(StoreAndForwardBase):
    """A table to hold all the messages"""
    id: int


class StoreAndForwardUpdate(StoreAndForwardBase):
    """Update the Store and Forward"""
    id: int | None = None
    msg_from: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None = None
    msg_to: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None = None
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)] | None = None
    packet: str | None = None
    relayed: bool | None = None
    relayed_at: float | None = None
    created: float | None = None
    network: str | None = None
