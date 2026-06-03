"""
ACARS Server
Background Tasks
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries

# Third Party Libraries

# Local Libraries
from acars_server import databases


class Adexp: # pragma: no cover
    """ADEXP messages"""

    def __init__(self, msg:databases.StoreAndForward) -> None:
        pass
