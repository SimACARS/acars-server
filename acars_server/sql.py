"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Annotated

# Third Party Libraries
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select

# Local Libraries


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
    last_used: float
