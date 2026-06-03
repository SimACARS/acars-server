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
from loguru import logger

# Local Libraries
from acars_server import databases
from tests.providers.general import AirlineProvider, MessageProvider, NetworkProvider

# Register Providers
factory.faker.Faker.add_provider(AirlineProvider)
factory.faker.Faker.add_provider(MessageProvider)
factory.faker.Faker.add_provider(NetworkProvider)

class MessageFactory(factory.Factory):
    """Factory for creating ApiKey instances for testing"""

    class Meta:
        """Meta class for ApiKeyFactory"""
        model = databases.StoreAndForward

    msg_from = factory.faker.Faker("message_from_atc")
    msg_to = factory.faker.Faker("full_callsign")
    msg_type = factory.faker.Faker("message_type")
    packet = factory.faker.Faker("message_packet")
    network = factory.faker.Faker("message_network")
    created = factory.LazyFunction(lambda: dt.now(tz.utc).timestamp())
    relayed = False
    relayed_at = 0.0

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(**kwargs)
        obj.save()
        logger.debug(obj)
        return obj
