"""
ACARS Server
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from pydantic_settings import BaseSettings

# Third Party Libraries

# Local Libraries

class Settings(BaseSettings):
    """Settings for ACARS Server"""
    testing: bool = False
