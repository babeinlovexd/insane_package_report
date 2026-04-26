import sys
from unittest.mock import MagicMock

def pytest_sessionstart(session):
    """Mock Home Assistant modules before tests start."""
    mock_modules = [
        "homeassistant",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.core",
        "homeassistant.helpers",
        "homeassistant.helpers.device_registry",
        "homeassistant.helpers.dispatcher",
        "homeassistant.helpers.storage",
    ]
    for module in mock_modules:
        sys.modules[module] = MagicMock()
