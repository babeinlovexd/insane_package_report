
import sys
from unittest.mock import MagicMock

# Comprehensive Mocking for Home Assistant
class MockModule(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

class MockInvalid(Exception):
    """Mock voluptuous.Invalid."""
    pass

def mock_homeassistant():
    sys.modules["homeassistant"] = MockModule()
    sys.modules["homeassistant.components"] = MockModule()
    sys.modules["homeassistant.components.sensor"] = MockModule()
    sys.modules["homeassistant.components.update"] = MockModule()
    sys.modules["homeassistant.config_entries"] = MockModule()
    sys.modules["homeassistant.const"] = MockModule()
    sys.modules["homeassistant.core"] = MockModule()
    sys.modules["homeassistant.data_entry_flow"] = MockModule()
    sys.modules["homeassistant.helpers"] = MockModule()
    sys.modules["homeassistant.helpers.aiohttp_client"] = MockModule()
    sys.modules["homeassistant.helpers.device_registry"] = MockModule()
    sys.modules["homeassistant.helpers.dispatcher"] = MockModule()
    sys.modules["homeassistant.helpers.entity_platform"] = MockModule()
    sys.modules["homeassistant.helpers.selector"] = MockModule()
    sys.modules["homeassistant.helpers.storage"] = MockModule()
    sys.modules["homeassistant.helpers.update_coordinator"] = MockModule()
    sys.modules["homeassistant.util"] = MockModule()
    sys.modules["homeassistant.util.dt"] = MockModule()

    vol_mock = MockModule()
    vol_mock.Invalid = MockInvalid
    sys.modules["voluptuous"] = vol_mock

mock_homeassistant()

import pytest
from custom_components.insane_updater.config_flow import validate_github_token
import voluptuous as vol

def test_validate_github_token_empty():
    """Test validation with empty token."""
    assert validate_github_token("") == ""
    assert validate_github_token(None) is None

def test_validate_github_token_classic():
    """Test validation with valid Classic PAT."""
    token = "ghp_" + "a" * 36
    assert validate_github_token(token) == token

def test_validate_github_token_fine_grained():
    """Test validation with valid Fine-grained PAT."""
    token = "github_pat_" + "b" * 22 + "_" + "c" * 59
    assert validate_github_token(token) == token

def test_validate_github_token_invalid_prefix():
    """Test validation with invalid prefix."""
    with pytest.raises(vol.Invalid):
        validate_github_token("abc_" + "a" * 36)

def test_validate_github_token_invalid_length_classic():
    """Test validation with invalid length for Classic PAT."""
    with pytest.raises(vol.Invalid):
        validate_github_token("ghp_" + "a" * 35)
    with pytest.raises(vol.Invalid):
        validate_github_token("ghp_" + "a" * 37)

def test_validate_github_token_invalid_length_fine_grained():
    """Test validation with invalid length for Fine-grained PAT."""
    with pytest.raises(vol.Invalid):
        token = "github_pat_" + "b" * 22 + "_" + "c" * 58
        validate_github_token(token)
    with pytest.raises(vol.Invalid):
        token = "github_pat_" + "b" * 21 + "_" + "c" * 59
        validate_github_token(token)

def test_validate_github_token_invalid_characters():
    """Test validation with invalid characters."""
    with pytest.raises(vol.Invalid):
        validate_github_token("ghp_" + "a" * 35 + "!")
