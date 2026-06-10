"""
ACARS Server
Testing
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import secrets
from datetime import datetime as dt, timezone as tz

# Third Party Libraries
import factory

# Local Libraries
from acars_server import auth, databases
from tests.providers.general import ATSUCallsignProvider, NetworkCidProvider, NetworkProvider

# Register Providers
factory.faker.Faker.add_provider(ATSUCallsignProvider)
factory.faker.Faker.add_provider(NetworkProvider)
factory.faker.Faker.add_provider(NetworkCidProvider)

AUTH = auth.Auth()


class ATSUOwnerFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating ATSU owner instances for testing"""

    class Meta:
        """Meta class for ApiKeyFactory"""
        model = databases.ATSUCallsignOwner
        sqlalchemy_session = databases.Session
        sqlalchemy_session_persistence = "flush"

    network = factory.faker.Faker("network")
    owner = factory.faker.Faker("owner")
    created = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    last_used = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    api_key = factory.LazyFunction(lambda: secrets.token_urlsafe(32))


class ATSUCallsignFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating ATSU callsigns instances for testing"""

    class Meta:
        """Meta class for ApiKeyFactory"""
        model = databases.ATSUCallsign
        sqlalchemy_session = databases.Session
        sqlalchemy_session_persistence = "flush"

    network = factory.faker.Faker("network")
    atsu_callsign = factory.faker.Faker("atsu_callsign")
    owner = factory.SubFactory(ATSUOwnerFactory)
    created = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    last_used = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())


class ATSUAuthorisedCallsignFactory(
    factory.alchemy.SQLAlchemyModelFactory):
    """ATSU ACF"""
    class Meta:
        """Meta"""
        model = databases.ATSUAuthorisedCallsign
        sqlalchemy_session = databases.Session
        sqlalchemy_session_persistence = "flush"

    network = factory.Faker("network")
    callsign = factory.Faker("authorised_callsigns")
    atsu_callsign = factory.SubFactory(ATSUCallsignFactory)
    owner = factory.SelfAttribute(
        "atsu_callsign.owner"
    )
    created = factory.LazyFunction(
        lambda: dt.now(tz.utc).timestamp()
    )
    last_used = factory.LazyFunction(
        lambda: dt.now(tz.utc).timestamp()
    )
