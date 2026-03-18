from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_GITHUB_TOKEN, EVENT_INSANE_PACKAGE_REPORT, SIGNAL_NEW_PACKAGE, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.UPDATE]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Insane Updater from a config entry."""

    token = entry.data.get(CONF_GITHUB_TOKEN, "")

    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "token": token,
        "store": store,
        "stored_data": stored_data,
        "coordinators": {}, # By (device_id, url)
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_package_report(event: Event) -> None:
        """Handle esphome.insane_package_report event."""

        # Event structure is:
        # device_id (usually added by esphome event mechanism if mapped to device,
        # but esphome events contain it in device_id or we need to find the device)
        # Event data: {"url": "...", "ref": "...", "type": "..."}

        data = event.data
        url = data.get("url")
        ref = data.get("ref", "")
        pkg_type = data.get("type", "packages")
        device_id = data.get("device_id")

        if not url or not device_id:
            _LOGGER.warning("Received invalid esphome.insane_package_report event: %s", data)
            return

        registry = dr.async_get(hass)
        device = registry.async_get(device_id)

        if not device:
            _LOGGER.warning("Device ID %s not found in registry", device_id)
            return

        _LOGGER.debug("Received package report for %s: %s @ %s", device.name, url, ref)

        # Notify the platform to create/update an entity
        async_dispatcher_send(
            hass,
            SIGNAL_NEW_PACKAGE,
            entry.entry_id,
            device_id,
            url,
            ref,
            pkg_type,
        )

    unsub = hass.bus.async_listen(EVENT_INSANE_PACKAGE_REPORT, handle_package_report)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        domain_data = hass.data[DOMAIN].pop(entry.entry_id)
        if "unsub" in domain_data:
            domain_data["unsub"]()

    return unload_ok
