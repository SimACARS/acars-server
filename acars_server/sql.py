"""
ACARS Server
SQL Connection and Models
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from datetime import datetime as dt, timezone as tz
from pathlib import Path
from typing import Annotated

# Third Party Libraries
import pandas as pd
from fastapi import Depends, Query
from pydantic import AfterValidator
from sqlmodel import Field, Session, SQLModel, create_engine

# Local Libraries
from acars_server import static_data


PWD = Path(os.path.dirname(__file__))
SQLITE_FILE_NAME = "database.db"
SQLITE_URL = f"sqlite:///{SQLITE_FILE_NAME}"

connect_args = {"check_same_thread": False}
engine = create_engine(SQLITE_URL, connect_args=connect_args)

def create_db_and_tables():
    """Create DB and Tables"""
    SQLModel.metadata.create_all(engine)

    # Output 1
    df = pd.read_csv(os.path.join(PWD.parent, "static_data_build", "built_data", "output_1.csv"))
    df.to_sql(name="cpdlc_uplink_message_elements", con=engine, if_exists="append", index=False)

    # Output 2
    df = pd.read_csv(os.path.join(PWD.parent, "static_data_build", "built_data", "output_2.csv"))
    df.to_sql(name="cpdlc_free_text_message_elements", con=engine, if_exists="append", index=False)

def get_session():
    """Get the Session"""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# ------------------------------------------------------------------
# API Key Models
# ------------------------------------------------------------------
class ApiKeyBase(SQLModel):
    """A table to hold all API keys"""
    api_key: str | None = Field(index=True)
    network: str | None


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
        raise ValueError(
            f"Invalid message type: Valid types are: {', '.join(static_data.LEGACY_MSG_TYPES)}")
    return legacy_type


class StoreAndForwardBase(SQLModel):
    """A table to hold all the messages"""
    msg_from: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None
    msg_to: Annotated[str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)] | None
    packet: str | None
    network: str | None

    def __getitem__(self, key):
        return getattr(self, key)


class StoreAndForward(StoreAndForwardBase, table=True):
    """A table to hold all the messages"""
    id: int | None = Field(default=None, primary_key=True)
    created: float
    relayed: bool | None = Field(default=None)
    relayed_at: float | None = Field(default=None)


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
    msg_from: Annotated[
        str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None = None
    msg_to: Annotated[
        str, Query(min_length=4, max_length=10, pattern="^[A-Z0-9]+$")] | None = None
    msg_type: Annotated[str, AfterValidator(check_valid_legacy_msg_type)] | None = None
    packet: str | None = None
    relayed: bool | None = None
    relayed_at: float | None = None
    created: float | None = None
    network: str | None = None
