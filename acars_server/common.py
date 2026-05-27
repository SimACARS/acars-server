"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import asyncio

# Third Party Libraries
from loguru import logger

# Init a message queue for web consumer
stream:asyncio.Queue = asyncio.Queue()

# Custom Loguru sink
LOG_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss!UTC}Z | {level} \t| "
    "{module}.{function}:{line} \t| {message}")


class QueueSink:
    """Handle moving logger to queue"""

    def write(self, message):
        """Write message to queue"""
        record = message.strip()
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(stream.put(record))
        except RuntimeError:
            pass

# Configure Loguru
logger.remove()
logger.add(
    QueueSink(),
    format=LOG_FORMAT
)
