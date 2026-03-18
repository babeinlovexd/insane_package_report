"""Update platform for Insane Updater."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.update import (
    UpdateDeviceClass,
    UpdateEntity,
    UpdateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .coordinator import InsaneUpdaterCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Update platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    # Add any entities that might already exist in memory (e.g. during a reload)
    packages_data = data["packages"]
    entities = []
    for device_id, packages in packages_data.items():
        for package in packages:
            entities.append(
                InsanePackageUpdateEntity(coordinator, device_id, package)
            )

    if entities:
        async_add_entities(entities)

    @callback
    def async_add_update_entity(package: dict[str, Any]) -> None:
        """Add update entity dynamically from dispatcher signal."""
        device_id = package.get("device_id")
        if device_id:
            async_add_entities([InsanePackageUpdateEntity(coordinator, device_id, package)])

    # Listen for the dispatcher signal to add entities dynamically
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_{entry.entry_id}_add_update_entity",
            async_add_update_entity
        )
    )

class InsanePackageUpdateEntity(CoordinatorEntity[InsaneUpdaterCoordinator], UpdateEntity):
    """Representation of an Update entity for a package."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_has_entity_name = True
    # We don't support installing from HA, only checking
    _attr_supported_features = UpdateEntityFeature(0)

    def __init__(
        self,
        coordinator: InsaneUpdaterCoordinator,
        device_id: str,
        package: dict[str, Any],
    ) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._package = package

        url = self._package.get("url", "unknown")
        ptype = self._package.get("type", "package")
        name = self._package.get("name", "unknown")

        self._attr_unique_id = f"{device_id}_{ptype}_{url}"

        # Name it nicely: e.g. "Package: esphome/packages"
        self._attr_name = f"{ptype.title()}: {name} ({url})"

        self._store_key = f"{device_id}_{ptype}_{url}"

        # Helper to get the store and installed versions
        data = coordinator.hass.data[DOMAIN][list(coordinator.hass.data[DOMAIN].keys())[0]]
        self._installed_versions = data.get("installed_versions", {})
        self._store = data.get("store")

    @property
    def device_info(self) -> dr.DeviceInfo | None:
        """Return device info to link this entity to the ESPHome device."""
        device_registry = dr.async_get(self.hass)
        device = device_registry.async_get(self._device_id)

        if device:
            return dr.DeviceInfo(
                identifiers=device.identifiers,
                connections=device.connections,
            )

        # Fallback if device somehow doesn't exist yet, though unlikely since ESPHome triggered it
        return dr.DeviceInfo(
            identifiers={("esphome", self._device_id)},
        )

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        if not self.coordinator.data:
            return None

        url = self._package.get("url")
        current_api_sha = self.coordinator.data.get(url)

        stored_sha = self._installed_versions.get(self._store_key)

        if stored_sha is None and current_api_sha is not None:
            # On first successful API response, save this as our baseline installed version
            self._installed_versions[self._store_key] = current_api_sha
            stored_sha = current_api_sha

            # Fire and forget save task
            if self._store:
                self.hass.async_create_task(self._store.async_save(self._installed_versions))

        ref = self._package.get("ref")
        base = ref if ref else "default"

        # If the stored_sha looks like "v1.0.0 (abcdef1)", it was fetched from the tags API.
        # We don't need to append base again.
        if stored_sha:
            if "(" in stored_sha:
                return stored_sha
            return f"{base} ({stored_sha})"
        return base

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if not self.coordinator.data:
            return None

        url = self._package.get("url")
        latest_sha = self.coordinator.data.get(url)

        if not latest_sha:
            return None

        ref = self._package.get("ref")
        base = ref if ref else "default"

        if "(" in latest_sha:
            return latest_sha

        return f"{base} ({latest_sha})"

    @property
    def title(self) -> str | None:
        """Title of the software."""
        return self._package.get("url")

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        url = self._package.get("url")
        if url:
            return f"https://github.com/{url}/commits"
        return None