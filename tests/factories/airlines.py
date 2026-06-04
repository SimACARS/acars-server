"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import os
import secrets
from datetime import datetime as dt, timezone as tz
from pathlib import Path

# Third Party Libraries
import factory

# Local Libraries
from acars_server import auth, databases
from tests.providers.general import AirlineProvider, DomainProvider, NetworkProvider

PWD = Path(os.path.dirname(__file__))

# Register Providers
factory.faker.Faker.add_provider(AirlineProvider)
factory.faker.Faker.add_provider(DomainProvider)
factory.faker.Faker.add_provider(NetworkProvider)

AUTH = auth.Auth()


class AirlineApiKeyFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating ApiKey instances for testing"""

    class Meta:
        """Meta class for ApiKeyFactory"""
        model = databases.AirlineApiKey
        sqlalchemy_session = databases.Session

    network = factory.faker.Faker("network")
    created = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    last_used = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    api_key = factory.LazyFunction(lambda: secrets.token_hex(64))
    verified = True
    airline_name = factory.faker.Faker("airline_name")
    airline_callsign = factory.faker.Faker("airline_coy_callsign")
    domain = factory.faker.Faker("domain")


class NewAirlineRequestFactory(factory.Factory):
    """Factory for creating Airline ICAO"""
    class Meta:
        """Meta"""
        model = databases.RequestNewAirline

    network = factory.faker.Faker("network")
    airline_name = factory.faker.Faker("airline_name")
    airline_callsign = factory.faker.Faker("airline_icao")
    domain = factory.faker.Faker("domain")
