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
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import UserApiKeyFactory

load_dotenv()

PWD = Path(os.path.dirname(__file__))
SQLITE_FILE_NAME = "test_database.db"
SQLITE_FILE_PATH = os.path.join(PWD.parent, SQLITE_FILE_NAME)
SQLITE_URL = f"sqlite:///{SQLITE_FILE_PATH}"

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

connect_args = {"check_same_thread": False}
engine = create_engine(SQLITE_URL, connect_args=connect_args)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create the test database schema before any tests run,
    and drop it after all tests are done.
    """
    if os.path.exists(SQLITE_FILE_PATH):
        os.remove(SQLITE_FILE_PATH)
        print(f"INFO: Removed existing test database at {SQLITE_FILE_PATH}")

    SQLModel.metadata.create_all(engine)  # Ensure the test database is created
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
