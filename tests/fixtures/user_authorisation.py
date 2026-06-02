"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Generator

# Third Party Libraries
import pytest
from fastapi.testclient import TestClient

# Local Libraries
from acars_server.databases import ApiKey
from tests.factories.user import ApiKeyFactory

@pytest.fixture(scope="function")
def aircraft_user(client: TestClient) -> Generator[TestClient, None, None]:
    """
    Fixture that returns a TestClient with authentication headers. It also creates a user in DB.
    """
    api_key: ApiKey = ApiKeyFactory()
    client.headers.update({"Authorization": f"Bearer {api_key.api_key}"})
    yield client
    # Clean up: Remove the headers after the test
    client.headers.clear()
