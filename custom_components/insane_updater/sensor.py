from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import DOMAIN, EVENT_INSANE_PACKAGE_REPORT

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sensor platform for Insane Updater Protocol."""

    entity = InsaneUpdaterProtocolSensor(hass, entry.entry_id)
    async_add_entities([entity])


class InsaneUpdaterProtocolSensor(SensorEntity):
    """A sensor that keeps a protocol log of all received ESPHome update events."""

    _attr_has_entity_name = True
    _attr_name = "Event Protocol"
    _attr_icon = "mdi:text-box-search-outline"

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialize the protocol sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._attr_unique_id = f"insane_updater_protocol_{entry_id}"

        self._log_entries: list[str] = []
        self._attr_native_value = "Waiting for events..."

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": "Insane Updater Service",
            "manufacturer": "BabeinlovexD",
        }

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes of the sensor."""
        return {
            "protocol_log": "\n".join(self._log_entries) if self._log_entries else "No events received since reboot."
        }

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""

        @callback
        def async_handle_event(event: Event) -> None:
            """Handle the incoming package report event."""
            data = event.data
            url = data.get("url", "unknown_url")
            device_id = data.get("device_id", "unknown_device")

            device_name = "Unknown ESP"
            if device_id != "unknown_device":
                registry = dr.async_get(self.hass)
                device = registry.async_get(device_id)
                if device:
                    device_name = device.name or device_name

            timestamp = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
            log_line = f"[{timestamp}] {device_name} reported: {url}"

            self._attr_native_value = f"{device_name} -> {url.split('/')[-1]}"

            self._log_entries.insert(0, log_line)
            if len(self._log_entries) > 50:
                self._log_entries.pop()

            self.async_write_ha_state()

        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_INSANE_PACKAGE_REPORT, async_handle_event)
        )
