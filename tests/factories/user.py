"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
import factory

# Local Libraries
from acars_server import auth, databases
from tests.providers.general import AirlineProvider, NetworkCidProvider, NetworkProvider

# Register Providers
factory.faker.Faker.add_provider(AirlineProvider)
factory.faker.Faker.add_provider(NetworkProvider)
factory.faker.Faker.add_provider(NetworkCidProvider)

AUTH = auth.Auth()


class UserApiKeyFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating ApiKey instances for testing"""

    class Meta:
        """Meta class for ApiKeyFactory"""
        model = databases.ApiKey
        sqlalchemy_session = databases.Session

    network = factory.faker.Faker("network")
    network_cid = factory.faker.Faker("network_cid")
    created = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    last_used = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    api_key = factory.LazyAttribute(
        lambda obj: AUTH.api_key_generator(
            uid=obj.network_cid,
            network=obj.network
        )
    )


class CallsignFactory(factory.Factory):
    """Factory for creating callsigns"""
    class Meta:
        """Meta"""
        model = dict
    callsign = factory.faker.Faker("full_callsign")


class CidFactory(factory.Factory):
    """Factory for creating CIDs"""
    class Meta:
        """Meta"""
        model = dict
    cid = factory.faker.Faker("network_cid")
