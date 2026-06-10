"""
ACARS Server
SQL Connection and Models
Chris Parkinson (@chssn)
"""

#!/usr/bin/env python3

# Standard Libraries
import random
from string import ascii_letters, digits, punctuation

# Third Party Libraries
import pytest

# Local Libraries
from acars_server.databases import check_valid_domain, check_valid_legacy_msg_type, check_valid_network
from acars_server.static_data import MSG_TYPES

@pytest.fixture
def character_map():
    """Character Map"""
    return ascii_letters + digits + punctuation

def test_check_valid_legacy_msg_type():
    """Test check_valid_legacy_msg_type"""
    test_value = random.choice(MSG_TYPES)
    output = check_valid_legacy_msg_type(test_value)
    assert output == test_value

def test_check_valid_legacy_msg_type_invalid_type(character_map):
    """Test check_valid_legacy_msg_type"""
    test_value = ''.join(random.choices(character_map, k=16))

    with pytest.raises(ValueError) as err:
        check_valid_legacy_msg_type(test_value)

    assert "Invalid message type" in str(err.value)

def test_check_valid_network_invalid_type(character_map):
    """Test check_valid_legacy_msg_type"""
    test_value = ''.join(random.choices(character_map, k=16))

    with pytest.raises(ValueError) as err:
        check_valid_network(test_value)

    assert "Invalid network" in str(err.value)

def test_check_valid_domain_invalid_type(character_map):
    """Test check_valid_legacy_msg_type"""
    test_gen = random.choice(punctuation),*[random.choice(character_map) for _ in range(15)]
    test_value = ''.join(test_gen) + ".com"

    with pytest.raises(ValueError) as err:
        check_valid_domain(test_value)

    assert "Invalid domain" in str(err.value)
