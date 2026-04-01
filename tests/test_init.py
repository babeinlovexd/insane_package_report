
import sys
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Mock Home Assistant modules before they are imported
mock_hass_module = MagicMock()
sys.modules["homeassistant"] = mock_hass_module
sys.modules["homeassistant.config_entries"] = MagicMock()
sys.modules["homeassistant.const"] = MagicMock()
sys.modules["homeassistant.core"] = MagicMock()
sys.modules["homeassistant.helpers"] = MagicMock()
sys.modules["homeassistant.helpers.device_registry"] = MagicMock()
sys.modules["homeassistant.helpers.dispatcher"] = MagicMock()
sys.modules["homeassistant.helpers.storage"] = MagicMock()

import unittest
from custom_components.insane_updater import async_setup_entry
from custom_components.insane_updater.const import DOMAIN, EVENT_INSANE_PACKAGE_REPORT, SIGNAL_NEW_PACKAGE

class TestInit(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.hass = MagicMock()
        self.hass.config_entries.async_forward_entry_setups = AsyncMock()
        self.hass.data = {}
        self.hass.bus.async_listen = MagicMock()

        self.entry = MagicMock()
        self.entry.entry_id = "test_entry"
        self.entry.options = {}
        self.entry.data = {}
        self.entry.add_update_listener = MagicMock()

    async def setup_integration(self):
        # Mock Store
        with patch("custom_components.insane_updater.Store") as mock_store:
            mock_store.return_value.async_load = AsyncMock(return_value={})
            await async_setup_entry(self.hass, self.entry)

        # Get the callback
        callback = None
        for call in self.hass.bus.async_listen.call_args_list:
            if call[0][0] == EVENT_INSANE_PACKAGE_REPORT:
                callback = call[0][1]
                break
        return callback

    async def test_handle_package_report_missing_url(self):
        """Test handle_package_report with missing url."""
        callback = await self.setup_integration()
        self.assertIsNotNone(callback)

        # Test missing url
        event = MagicMock()
        event.event_type = EVENT_INSANE_PACKAGE_REPORT
        event.data = {"device_id": "test_device"}

        with patch("custom_components.insane_updater._LOGGER.error") as mock_error, \
             patch("custom_components.insane_updater.async_dispatcher_send") as mock_send:
            await callback(event)
            mock_error.assert_called_with("Insane Updater failed to process event: Missing 'url' in event data: %s", event.data)
            mock_send.assert_not_called()

    async def test_handle_package_report_missing_device_id(self):
        """Test handle_package_report with missing device_id."""
        callback = await self.setup_integration()
        self.assertIsNotNone(callback)

        # Test missing device_id
        event = MagicMock()
        event.event_type = EVENT_INSANE_PACKAGE_REPORT
        event.data = {"url": "http://github.com/repo"}

        with patch("custom_components.insane_updater._LOGGER.error") as mock_error, \
             patch("custom_components.insane_updater.async_dispatcher_send") as mock_send:
            await callback(event)
            mock_error.assert_called_with("Insane Updater failed to process event: Missing 'device_id' in event data. The ESPHome device must be properly linked in Home Assistant. Event data: %s", event.data)
            mock_send.assert_not_called()

    async def test_handle_package_report_device_not_found(self):
        """Test handle_package_report when device is not found in registry."""
        callback = await self.setup_integration()
        self.assertIsNotNone(callback)

        # Mock device registry to return None
        mock_registry = MagicMock()
        mock_registry.async_get.return_value = None

        with patch("custom_components.insane_updater.dr.async_get", return_value=mock_registry):
            event = MagicMock()
            event.event_type = EVENT_INSANE_PACKAGE_REPORT
            event.data = {"url": "http://github.com/repo", "device_id": "non_existent_device"}

            with patch("custom_components.insane_updater._LOGGER.error") as mock_error, \
                 patch("custom_components.insane_updater.async_dispatcher_send") as mock_send:
                await callback(event)
                mock_error.assert_called_with("Insane Updater: Device ID '%s' not found in Home Assistant Device Registry. Cannot attach entity for URL: %s", "non_existent_device", "http://github.com/repo")
                mock_send.assert_not_called()

    async def test_handle_package_report_success(self):
        """Test handle_package_report success path."""
        callback = await self.setup_integration()
        self.assertIsNotNone(callback)

        # Mock device
        mock_device = MagicMock()
        mock_device.name = "Test ESP"
        mock_device.name_by_user = None
        mock_device.sw_version = "1.2.3"

        mock_registry = MagicMock()
        mock_registry.async_get.return_value = mock_device

        with patch("custom_components.insane_updater.dr.async_get", return_value=mock_registry):
            event = MagicMock()
            event.event_type = EVENT_INSANE_PACKAGE_REPORT
            event.data = {
                "url": "http://github.com/repo",
                "device_id": "test_device",
                "ref": "main",
                "type": "packages"
            }

            with patch("custom_components.insane_updater.async_dispatcher_send") as mock_send:
                await callback(event)
                mock_send.assert_called_with(
                    self.hass,
                    SIGNAL_NEW_PACKAGE,
                    self.entry.entry_id,
                    "test_device",
                    "http://github.com/repo",
                    "main",
                    "packages",
                    "1.2.3"
                )
