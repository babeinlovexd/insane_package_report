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
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import Store

from .const import DOMAIN, SIGNAL_NEW_PACKAGE
from .coordinator import GitHubPackageCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Update platform for Insane Updater."""

    @callback
    def async_add_package_entity(entry_id, device_id, url, ref, pkg_type):
        """Add a new package entity if it doesn't exist."""
        if entry.entry_id != entry_id:
            return

        domain_data = hass.data[DOMAIN][entry.entry_id]
        coordinators = domain_data["coordinators"]
        store = domain_data["store"]
        stored_data = domain_data["stored_data"]

        entity_id = f"{device_id}_{url}"

        if entity_id in coordinators:
            # Entity already exists, just update installed version if needed
            entity = coordinators[entity_id]["entity"]
            entity.async_update_installed_version(ref)
            return

        coordinator = GitHubPackageCoordinator(
            hass, domain_data["token"], url, ref, pkg_type
        )

        entity = InsanePackageUpdateEntity(
            coordinator, device_id, url, ref, pkg_type, store, stored_data
        )

        coordinators[entity_id] = {"coordinator": coordinator, "entity": entity}

        async_add_entities([entity])
        hass.async_create_task(coordinator.async_config_entry_first_refresh())

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_PACKAGE, async_add_package_entity
        )
    )


class InsanePackageUpdateEntity(CoordinatorEntity[GitHubPackageCoordinator], UpdateEntity):
    """Representation of an Insane Package Update entity."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES | UpdateEntityFeature.INSTALL

    def __init__(
        self,
        coordinator: GitHubPackageCoordinator,
        device_id: str,
        url: str,
        ref: str,
        pkg_type: str,
        store: Store,
        stored_data: dict,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._url = url
        self._ref = ref
        self._pkg_type = pkg_type
        self._store = store
        self._stored_data = stored_data

        # Load installed version from store
        store_key = f"{self._device_id}_{self._url}"
        self._store_key = store_key

        # We start with the stored installed SHA if available, otherwise we'll resolve it
        if store_key in self._stored_data:
            self._installed_version = self._stored_data[store_key]
        else:
            self._installed_version = None

        # To track when the ESP reports a new ref
        self._current_ref = self._ref

        # Generate unique ID based on device and URL
        # Extract repo name for naming
        repo_name = self._url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        self._attr_unique_id = f"insane_updater_{self._device_id}_{self._url}"
        self._attr_name = f"{repo_name} Update"

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        registry = dr.async_get(self.hass)
        device = registry.async_get(self._device_id)
        if device:
            return {
                "identifiers": device.identifiers,
                "connections": device.connections,
            }

        # Fallback if device somehow not found, though we checked in __init__.py
        return {
            "identifiers": {("esphome", self._device_id)},
            "default_manufacturer": "ESPHome",
            "default_model": "Custom Component",
        }

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_commit")
        return None

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        if self.coordinator.data:
            return self.coordinator.data.get("release_url")
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if not self.coordinator.data:
            return

        latest_commit = self.coordinator.data.get("latest_commit")

        # If we have no installed version stored, assume the current latest commit is the installed one.
        # This handles the initial setup where we only know the 'ref' from the ESP,
        # but we need to store the actual SHA to track future updates.
        if self._installed_version is None and latest_commit:
            self._installed_version = latest_commit
            self._stored_data[self._store_key] = self._installed_version
            self.hass.async_create_task(self._store.async_save(self._stored_data))

        super()._handle_coordinator_update()

    @callback
    def async_update_installed_version(self, new_ref: str) -> None:
        """Called when ESP reports an event. We check if the ref changed."""
        if self._current_ref != new_ref:
            # The ESP reported a different ref (e.g. user changed from 'main' to 'dev' in YAML).
            # We don't know the SHA yet, so we clear the installed version.
            # Next coordinator update will fetch the latest SHA for the new ref and set it as installed.
            self._current_ref = new_ref
            self.coordinator.ref = new_ref # Update coordinator's ref to fetch correct data
            self._installed_version = None
            self.hass.async_create_task(self.coordinator.async_request_refresh())

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Mark as installed. Usually called when user manually clicks Install in HA."""
        if self.latest_version:
            self._installed_version = self.latest_version
            self._stored_data[self._store_key] = self._installed_version
            await self._store.async_save(self._stored_data)
            self.async_write_ha_state()
