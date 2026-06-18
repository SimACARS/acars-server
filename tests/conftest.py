"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import csv
import os
import re
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
from acars_server.databases import CPDLCTypes, get_session
from tests.factories.atsu import (
    ATSUAuthorisedCallsignFactory,
    ATSUCallsignFactory,
    ATSUOwnerFactory)
from tests.factories.airlines import AirlineApiKeyFactory
from tests.factories.user import UserApiKeyFactory

PWD = Path(os.path.dirname(__file__))

if os.getenv("RUNNING_IN_DOCKER", "").lower() == "true":
    load_dotenv()
else:
    load_dotenv(os.path.join(PWD.parent, "acars_server", ".env"))

DATABASE_HOST = os.getenv("MYSQL_HOST")
DATABASE_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DATABASE_NAME = os.getenv("MYSQL_DB")
DATABASE_USER = os.getenv("MYSQL_USER")
DATABASE_PASSWORD = os.getenv("MYSQL_PASSWORD")

DATABASE_URL = (
    f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}_test"
)

redis_db = get_redis_connection(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD"),
    username="default",
    decode_responses=True
)

redis_async_db = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT", "6379")),
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
    if os.getenv("RUNNING_IN_DOCKER", "").lower() == "true":
        with Session(engine) as session:
            data_to_build = [
                os.path.join(PWD.parent, "static_data_build", "built_data", "output_1.csv"),
                os.path.join(PWD.parent, "static_data_build", "built_data", "output_2.csv")
            ]

            for file in data_to_build:
                with open(file, "r", encoding="utf-8") as f:
                    read_csv = csv.DictReader(f)
                    for line in read_csv:
                        # Extract Ref
                        ref = re.match(r"^([UD]M)\s*([0-9]{1,3}[a-z]{0,2})$", line["Ref"])

                        if ref:
                            data = {
                                "direction": ref.group(1),
                                "reference_number": f"{ref.group(1)}{ref.group(2)}",
                                "message_intent": line["Message Intent"],
                                "message_element": line["Message Element"],
                                "response_type": line["Resp"],
                                "fans_1_a": False,
                                "fans_1_a_atn_b1": False,
                                "atn_b1": False
                            }

                            # Extract Data Link Systems
                            if line.get("Data link system"):
                                if "FANS 1/A- ATN B1" in line["Data link system"]:
                                    data["fans_1_a_atn_b1"] = True
                                if re.match(r"FANS 1/A(?!-)", line["Data link system"]):
                                    data["fans_1_a"] = True
                                if re.match(r"(?<=A-\s)ATN B1", line["Data link system"]):
                                    data["atn_b1"] = True
                            else:
                                data["fans_1_a_atn_b1"] = True
                                data["fans_1_a"] = True
                                data["atn_b1"] = True

                            db_add = CPDLCTypes.model_validate(data)
                            session.add(db_add)
                            session.commit()
                            session.refresh(db_add)

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
