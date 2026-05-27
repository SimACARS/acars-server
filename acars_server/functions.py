"""
ACARS Server
Common Functions
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import time
from collections import deque
from typing import Any, Dict

# Third Party Libraries
import requests # type: ignore
from loguru import logger

# Local Libraries


class RateLimiter:
    """A rate limiter"""
    def __init__(self, window_minutes: int, limit: int):
        self.window = window_minutes * 60  # convert to seconds
        self.limit = limit
        self.requests:deque = deque()

    def is_rate_limited(self) -> bool:
        """Check if a rate limit has been exceeded"""
        now = time.time()

        # Remove old requests outside the window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        # Check limit
        if len(self.requests) >= self.limit:
            return True

        # Record this request
        self.requests.append(now)
        return False


def load_json_url(url: str, timeout: int = 5, headers: dict|None = None) -> Dict[str, Any]:
    """Requests a json page and returns the output"""
    try:
        if not headers:
            response = requests.get(url, {"Content-type": "application/json"}, timeout=timeout)
        else:
            response = requests.get(
                url, {"Content-type": "application/json"}, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.json()
        logger.warning(f"{url} returned status code {response.status_code}")
    except requests.JSONDecodeError as err:
        logger.warning(f"{err} - {url}")
    except requests.ReadTimeout as err:
        logger.warning(f"{err} - {url}")
    return {}
