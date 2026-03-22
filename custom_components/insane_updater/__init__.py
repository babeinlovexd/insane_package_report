# https://github.com/babeinlovexd

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, Event
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DOMAIN, CONF_GITHUB_TOKEN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, EVENT_INSANE_PACKAGE_REPORT, SIGNAL_NEW_PACKAGE, STORAGE_KEY, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.UPDATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Insane Updater from a config entry."""

    token = entry.options.get(CONF_GITHUB_TOKEN, entry.data.get(CONF_GITHUB_TOKEN, ""))
    update_interval_str = entry.options.get(
        CONF_UPDATE_INTERVAL, entry.data.get(CONF_UPDATE_INTERVAL, str(DEFAULT_UPDATE_INTERVAL))
    )
    update_interval = int(update_interval_str)

    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    stored_data = await store.async_load() or {}

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "token": token,
        "update_interval": update_interval,
        "store": store,
        "stored_data": stored_data,
        "coordinators": {},
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    async def handle_package_report(event: Event) -> None:
        """Handle esphome.insane_package_report event."""

        data = event.data
        _LOGGER.debug("Insane Updater received event: %s with data: %s", event.event_type, data)

        url = data.get("url")
        ref = data.get("ref", "")
        pkg_type = data.get("type", "packages")
        device_id = data.get("device_id")

        if not url:
            _LOGGER.error("Insane Updater failed to process event: Missing 'url' in event data: %s", data)
            return

        if not device_id:
            _LOGGER.error("Insane Updater failed to process event: Missing 'device_id' in event data. The ESPHome device must be properly linked in Home Assistant. Event data: %s", data)
            return

        registry = dr.async_get(hass)
        device = registry.async_get(device_id)

        if not device:
            _LOGGER.error("Insane Updater: Device ID '%s' not found in Home Assistant Device Registry. Cannot attach entity for URL: %s", device_id, url)
            return

        device_name = device.name_by_user or device.name or "Unknown ESP"

        _LOGGER.info("Insane Updater successfully parsed package report for %s (ID: %s): %s @ %s", device_name, device_id, url, ref)

        sw_version = device.sw_version or "unknown_compile_time"

        async_dispatcher_send(
            hass,
            SIGNAL_NEW_PACKAGE,
            entry.entry_id,
            device_id,
            url,
            ref,
            pkg_type,
            sw_version,
        )

    unsub = hass.bus.async_listen(EVENT_INSANE_PACKAGE_REPORT, handle_package_report)
    hass.data[DOMAIN][entry.entry_id]["unsub"] = unsub

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        domain_data = hass.data[DOMAIN].pop(entry.entry_id)
        if "unsub" in domain_data:
            domain_data["unsub"]()

    return unload_ok
