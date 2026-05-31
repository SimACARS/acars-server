"""
ACARS Server
APP Server Status
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from typing import Any

responses_user_new_network:dict[int|str,dict[str,Any]]|None  = {
    307: {},
    400: {},
    501: {},
}
