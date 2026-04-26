
import sys
import logging
from unittest.mock import MagicMock, patch, AsyncMock
import unittest

# Define dummy classes to avoid metaclass conflicts
class SubscriptableType(type):
    def __getitem__(cls, item):
        return cls

class MockCoordinatorEntity(metaclass=SubscriptableType):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.hass = coordinator.hass

    def _handle_coordinator_update(self) -> None:
        pass

class MockUpdateEntity:
    _attr_device_class = None
    _attr_supported_features = 0
    _attr_icon = None
    _attr_has_entity_name = False

    def async_write_ha_state(self):
        pass

# Mock modules
mock_ha = MagicMock()
# Mock @callback decorator to just return the function
mock_ha.core.callback = lambda f: f

sys.modules["homeassistant"] = mock_ha
sys.modules["homeassistant.components"] = mock_ha.components
sys.modules["homeassistant.components.update"] = mock_ha.components.update
sys.modules["homeassistant.components.update"].UpdateEntity = MockUpdateEntity
sys.modules["homeassistant.components.update"].UpdateDeviceClass = MagicMock()
sys.modules["homeassistant.components.update"].UpdateEntityFeature = MagicMock()

sys.modules["homeassistant.helpers"] = mock_ha.helpers
sys.modules["homeassistant.helpers.update_coordinator"] = mock_ha.helpers.update_coordinator
sys.modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = MockCoordinatorEntity

sys.modules["homeassistant.config_entries"] = mock_ha.config_entries
sys.modules["homeassistant.const"] = mock_ha.const
sys.modules["homeassistant.core"] = mock_ha.core
sys.modules["homeassistant.helpers.entity_platform"] = mock_ha.helpers.entity_platform
sys.modules["homeassistant.helpers.device_registry"] = mock_ha.helpers.device_registry
sys.modules["homeassistant.helpers.dispatcher"] = mock_ha.helpers.dispatcher
sys.modules["homeassistant.helpers.storage"] = mock_ha.helpers.storage
sys.modules["homeassistant.helpers.aiohttp_client"] = mock_ha.helpers.aiohttp_client
sys.modules["homeassistant.util"] = mock_ha.util

# Re-import after mocking
from custom_components.insane_updater.update import InsanePackageUpdateEntity

class TestPerformance(unittest.TestCase):
    def setUp(self):
        self.coordinator = MagicMock()
        self.coordinator.hass = MagicMock()
        self.coordinator.data = {"latest_version": "main (abcdef1)"}

        self.store = MagicMock()
        self.store.async_save = AsyncMock()

        self.stored_data = {}

        # We need to mock slugify because it's used in __init__
        with patch("custom_components.insane_updater.update.slugify", side_effect=lambda x: x), \
             patch("custom_components.insane_updater.update.parse_github_url", return_value=("owner", "repo")):
            self.entity = InsanePackageUpdateEntity(
                self.coordinator,
                "device_id",
                "https://github.com/owner/repo",
                "main",
                "packages",
                self.store,
                self.stored_data,
                "1.0.0"
            )
            # Ensure entity.hass is correctly set
            self.entity.hass = self.coordinator.hass

    def test_property_side_effect_removed(self):
        # Initial state - __init__ sets it to self._ref ("main") if not in stored_data
        self.assertEqual(self.entity._installed_version, "main")

        # Accessing the property should NO LONGER trigger async_create_task
        with patch.object(self.entity.hass, "async_create_task") as mock_create_task:
            version = self.entity.installed_version
            self.assertEqual(version, "main") # Should still be "main" until coordinator update
            self.assertEqual(mock_create_task.call_count, 0)

    def test_coordinator_update_triggers_save(self):
        # Initial state
        self.assertEqual(self.entity._installed_version, "main")

        # Simulate coordinator update
        with patch.object(self.entity.hass, "async_create_task") as mock_create_task:
            self.entity._handle_coordinator_update()

            # Check if _installed_version was updated
            self.assertEqual(self.entity._installed_version, "main (abcdef1)")

            # Check if storage save was triggered
            mock_create_task.assert_called_once()

            # Verify property returns updated version
            self.assertEqual(self.entity.installed_version, "main (abcdef1)")

    def test_hass_none_guard_coordinator_update(self):
        """Test that _handle_coordinator_update doesn't crash if hass is None."""
        self.entity.hass = None
        try:
            self.entity._handle_coordinator_update()
        except AttributeError as e:
            self.fail(f"_handle_coordinator_update crashed with AttributeError: {e}")

    def test_hass_none_guard_sw_version_update(self):
        """Test that async_update_device_sw_version doesn't crash if hass is None."""
        self.entity.hass = None
        try:
            self.entity.async_update_device_sw_version("2.0.0")
        except AttributeError as e:
            self.fail(f"async_update_device_sw_version crashed with AttributeError: {e}")

if __name__ == "__main__":
    unittest.main()
