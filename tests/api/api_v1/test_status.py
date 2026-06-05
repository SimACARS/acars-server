"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries
from fastapi.testclient import TestClient

# Local Libraries
from acars_server import __VERSION__

def test_status_message(client: TestClient):
    """Tests the status message"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["server_status"] == "OK"
    assert response.json()["server_version"] == __VERSION__
