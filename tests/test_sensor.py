
import sys
from unittest.mock import MagicMock, patch

# Define a dummy SensorEntity class
class MockSensorEntity:
    def __init__(self):
        self.hass = None
        self._attr_native_value = None

    def async_write_ha_state(self):
        pass

    def async_on_remove(self, unsub):
        pass

# Mock Home Assistant modules
mock_ha = MagicMock()
mock_ha.core.callback = lambda f: f
sys.modules["homeassistant"] = mock_ha
sys.modules["homeassistant.components"] = mock_ha.components
sys.modules["homeassistant.components.sensor"] = mock_ha.components.sensor
sys.modules["homeassistant.components.sensor"].SensorEntity = MockSensorEntity
sys.modules["homeassistant.config_entries"] = mock_ha.config_entries
sys.modules["homeassistant.const"] = mock_ha.const
sys.modules["homeassistant.core"] = mock_ha.core
sys.modules["homeassistant.helpers"] = mock_ha.helpers
sys.modules["homeassistant.helpers.device_registry"] = mock_ha.helpers.device_registry
sys.modules["homeassistant.helpers.entity_platform"] = mock_ha.helpers.entity_platform
sys.modules["homeassistant.util"] = mock_ha.util
sys.modules["homeassistant.util.dt"] = mock_ha.util.dt

import unittest
from datetime import datetime
from custom_components.insane_updater.sensor import InsaneUpdaterProtocolSensor
from custom_components.insane_updater.const import EVENT_INSANE_PACKAGE_REPORT

class TestSensor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = MagicMock()
        # Mock device registry to return None (Unknown ESP)
        self.mock_dr = MagicMock()
        self.mock_dr.async_get.return_value = None

        # Patching dr.async_get inside the test class scope
        self.patcher = patch("custom_components.insane_updater.sensor.dr.async_get", return_value=self.mock_dr)
        self.patcher.start()

        self.sensor = InsaneUpdaterProtocolSensor(self.hass, "test_entry")

        # Mock dt_util.now()
        self.now = datetime(2024, 1, 1, 12, 0, 0)
        mock_ha.util.dt.now.return_value = self.now

    def tearDown(self):
        self.patcher.stop()

    async def test_sensor_init(self):
        """Test sensor initialization."""
        self.assertEqual(self.sensor._attr_name, "Event Protocol")
        self.assertEqual(self.sensor._attr_native_value, "Waiting for events...")
        self.assertEqual(self.sensor._attr_unique_id, "insane_updater_protocol_test_entry")

    async def test_sensor_handle_event_invalid_url(self):
        """Test sensor handling an event with an invalid GitHub URL."""
        # Setup event listener
        await self.sensor.async_added_to_hass()

        # Capture the callback
        callback = None
        for call in self.hass.bus.async_listen.call_args_list:
            if call[0][0] == EVENT_INSANE_PACKAGE_REPORT:
                callback = call[0][1]
                break

        self.assertIsNotNone(callback)

        # Trigger the callback with invalid URL
        event = MagicMock()
        event.data = {
            "url": "my-invalid-repo",
            "device_id": "unknown_device"
        }

        callback(event)

        # Verify fallback logic: url.split("/")[-1] -> "my-invalid-repo"
        self.assertEqual(self.sensor._attr_native_value, "Unknown ESP -> my-invalid-repo")

        # Test another invalid URL with slashes
        event.data["url"] = "https://github.com/invalid"
        callback(event)
        self.assertEqual(self.sensor._attr_native_value, "Unknown ESP -> invalid")

    async def test_sensor_handle_event_valid_url(self):
        """Test sensor handling an event with a valid GitHub URL."""
        # Setup event listener
        await self.sensor.async_added_to_hass()

        # Capture the callback
        callback = None
        for call in self.hass.bus.async_listen.call_args_list:
            if call[0][0] == EVENT_INSANE_PACKAGE_REPORT:
                callback = call[0][1]
                break

        self.assertIsNotNone(callback)

        # Trigger the callback with valid URL
        event = MagicMock()
        event.data = {
            "url": "https://github.com/owner/repo",
            "device_id": "unknown_device"
        }

        callback(event)

        # Verify repo_name extraction
        self.assertEqual(self.sensor._attr_native_value, "Unknown ESP -> repo")

if __name__ == "__main__":
    unittest.main()
