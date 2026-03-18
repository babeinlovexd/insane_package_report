"""The Insane Updater integration."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.dispatcher import async_dispatcher_send

from homeassistant.helpers.storage import Store

from .const import DOMAIN, ESPHOME_EVENT, CONF_GITHUB_TOKEN
from .coordinator import InsaneUpdaterCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["update"]
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.installed_versions"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Load persisted installed versions
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    installed_versions = await store.async_load()
    if installed_versions is None:
        installed_versions = {}
    """Set up Insane Updater from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    token = entry.data.get(CONF_GITHUB_TOKEN)
    coordinator = InsaneUpdaterCoordinator(hass, token)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "packages": {}, # Dict structure: {device_id: [packages...]}
        "installed_versions": installed_versions,
        "store": store
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the event listener for ESPHome events
    async def handle_esphome_event(event: Event) -> None:
        """Handle incoming insane_package_report events from ESPHome."""
        device_id = event.data.get("device_id")

        # ESPHome sends a data payload which contains a JSON string
        try:
            # First extract the raw string from the data dictionary
            raw_data = event.data.get("data", "")

            # If it's a string, try parsing it as JSON
            if isinstance(raw_data, str) and raw_data.startswith("{"):
                payload = json.loads(raw_data)
            else:
                # Fallback if it's already a dict somehow
                payload = raw_data if isinstance(raw_data, dict) else {}

        except json.JSONDecodeError:
            _LOGGER.error("Failed to decode JSON payload from event data: %s", event.data.get("data"))
            return

        if not device_id or not payload or "url" not in payload:
            _LOGGER.debug("Received invalid event payload: %s", event.data)
            return

        _LOGGER.debug("Received update report from device %s: %s", device_id, payload)

        data = hass.data[DOMAIN][entry.entry_id]
        if device_id not in data["packages"]:
            data["packages"][device_id] = []

        # Check if we already have this package for this device to avoid duplicates
        exists = any(p.get("url") == payload.get("url") and p.get("type") == payload.get("type")
                     for p in data["packages"][device_id])

        if not exists:
            # Add device_id to the payload so the update entity knows where to attach itself
            payload["device_id"] = device_id
            data["packages"][device_id].append(payload)

            # Add to coordinator to track version updates
            coordinator.add_repository(payload)

            # Trigger a coordinator refresh to immediately check the newly added repo
            hass.async_create_task(coordinator.async_request_refresh())

            _LOGGER.info("Registered new repository %s for device %s", payload.get("url"), device_id)

            # Use dispatcher to add the entity dynamically without requiring a reload
            async_dispatcher_send(
                hass,
                f"{DOMAIN}_{entry.entry_id}_add_update_entity",
                payload
            )

    # Listen for the event that ESPHome sends
    entry.async_on_unload(
        hass.bus.async_listen(ESPHOME_EVENT, handle_esphome_event)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok