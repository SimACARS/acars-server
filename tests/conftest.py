"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
from pathlib import Path
from typing import Generator

# Third Party Libraries
import pytest
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import testclient
from redis_om import get_redis_connection, Migrator
from sqlmodel import Session, SQLModel, create_engine

# Local Libraries
from acars_server.__main__ import app, settings
from acars_server.databases import get_session
from tests.factories.atsu import (
    ATSUAuthorisedCallsignFactory,
    ATSUCallsignFactory,
    ATSUOwnerFactory)
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import UserApiKeyFactory

load_dotenv()

PWD = Path(os.path.dirname(__file__))
DATABASE_HOST = os.getenv("MYSQL_HOST", "localhost")
DATABASE_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DATABASE_NAME = os.getenv("MYSQL_DB", "acars")
DATABASE_USER = os.getenv("MYSQL_USER", "acars")
DATABASE_PASSWORD = os.getenv("MYSQL_PASSWORD")

DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}_test"
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

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create the test database schema before any tests run,
    and drop it after all tests are done.
    """
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)  # Ensure the test database is created
    Migrator().run()
    yield

@pytest.fixture(scope="function", autouse=True)
def clear_redis_cache():
    """Clears the redis cache"""
    redis_db.flushall()
    Migrator().run()
    yield

@pytest.fixture(scope="session", autouse=True)
def enable_test_mode():
    """Enable test mode for the duration of the tests"""
    print("INFO: Enabling test mode for the duration of the tests")
    settings.testing = True
    yield
    print("INFO: Disabling test mode after tests complete")
    settings.testing = False

@pytest.fixture(scope="function")
def db() -> Generator:
    """
    Create a new database session for each test and roll it back after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    print("INFO: Starting a new database session for a test")
    with Session(bind=connection) as session:
        yield session
    print("INFO: Rolling back the database session after the test")
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(autouse=True)
def set_session_for_factories(db: Session):
    """Factory Session Fixture"""
    print("INFO: Setting the database session for factories")
    AirlineApiKeyFactory._meta.sqlalchemy_session = db
    UserApiKeyFactory._meta.sqlalchemy_session = db
    ATSUOwnerFactory._meta.sqlalchemy_session = db
    ATSUCallsignFactory._meta.sqlalchemy_session = db
    ATSUAuthorisedCallsignFactory._meta.sqlalchemy_session = db

@pytest.fixture(scope="function")
def client(db: Session) -> Generator[testclient.TestClient, None, None]:
    """
    Provide a TestClient that uses the test database session.
    """
    print("INFO: Providing a TestClient for a test")
    def override_get_db():
        yield db
    app.dependency_overrides[get_session] = override_get_db

    with testclient.TestClient(app, base_url="http://127.0.0.1:8000") as test_client:
        yield test_client

    app.dependency_overrides.clear()
