"""
ACARS Server
Common Functions
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Any, Dict

# Third Party Libraries
import requests # type: ignore
from loguru import logger

# Local Libraries


def load_json_url(
        url: str,
        timeout: int = 5,
        headers: dict|None = None) -> Dict[str, Any]: # pragma: no cover
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

async def _ensure_group(redis, stream: str, group: str): # pragma: no cover
    """Add a group"""
    try:
        await redis.xgroup_create(
            name=stream,
            groupname=group,
            id="0",  # only new messages from now
            mkstream=True
        )
        await redis.xtrim(stream, maxlen=1000)
    except Exception as e:
        if "BUSYGROUP" not in str(e):
            raise

_ensure_store = set()

async def ensure_group_once(redis, stream, group): # pragma: no cover
    """Ensure the group exists in Redis."""
    if group in _ensure_store:
        return
    _ensure_store.add(group)
    await _ensure_group(redis, stream, group)

async def stream_messages(redis, stream: str, group: str, consumer: str): # pragma: no cover
    """Stream Messages"""
    while True:
        resp = await redis.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: ">"},  # only THIS callsign stream
            count=10,
            block=5000,
        )

        if not resp:
            continue

        for _, messages in resp:
            for msg_id, fields in messages:
                yield msg_id, fields
                await redis.xack(stream, group, msg_id)
