from __future__ import annotations

import logging

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
    def async_add_package_entity(entry_id, device_id, url, ref, pkg_type, sw_version):
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
            if coordinators[entity_id] is not None:
                entity = coordinators[entity_id]["entity"]
                entity.async_update_device_sw_version(sw_version)
            return

        # Mark as being processed to prevent duplicate creation
        coordinators[entity_id] = None

        coordinator = GitHubPackageCoordinator(
            hass, domain_data["token"], url, ref, pkg_type, domain_data["update_interval"]
        )

        # FIX: Sofort registrieren, niemals auf GitHub warten!
        entity = InsanePackageUpdateEntity(
            coordinator, device_id, url, ref, pkg_type, store, stored_data, sw_version
        )

        coordinators[entity_id] = {"coordinator": coordinator, "entity": entity}

        # 1. Sofort an HA übergeben
        async_add_entities([entity])

        # 2. Asynchron laden lassen
        hass.async_create_task(coordinator.async_request_refresh())

    entry.async_on_unload(
        async_dispatcher_connect(
            hass, SIGNAL_NEW_PACKAGE, async_add_package_entity
        )
    )


class InsanePackageUpdateEntity(CoordinatorEntity[GitHubPackageCoordinator], UpdateEntity):
    """Representation of an Insane Package Update entity."""

    _attr_device_class = UpdateDeviceClass.FIRMWARE
    _attr_supported_features = UpdateEntityFeature(0)
    _attr_icon = "mdi:github"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GitHubPackageCoordinator,
        device_id: str,
        url: str,
        ref: str,
        pkg_type: str,
        store: Store,
        stored_data: dict,
        sw_version: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device_id = device_id
        self._url = url
        self._ref = ref
        self._pkg_type = pkg_type
        self._store = store
        self._stored_data = stored_data
        self._sw_version = sw_version

        # Load installed version and previous sw_version from store
        self._store_key = f"{self._device_id}_{self._url}"
        self._sw_store_key = f"sw_{self._device_id}"

        self._installed_version = self._stored_data.get(self._store_key)

        # If we just booted, we check if the ESPHome compilation time (sw_version) changed.
        # If it changed, we assume the user flashed the device with the newest code.
        previous_sw_version = self._stored_data.get(self._sw_store_key)

        if previous_sw_version != self._sw_version:
            # The user re-compiled and flashed the ESP! Clear the installed version
            # so it syncs up with whatever GitHub's latest version is on the first fetch.
            self._installed_version = None

            # Save the new firmware version
            self._stored_data[self._sw_store_key] = self._sw_version
            self.hass.async_create_task(self._store.async_save(self._stored_data))

        if not self._installed_version:
            self._installed_version = self._ref if self._ref else "main"

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

        # When attaching entities to an existing device created by another integration
        # (like ESPHome), we ONLY provide the identifiers. Providing anything else,
        # especially connections, causes the device registry to update the device and
        # can break the original integration's connection.
        if device:
            # We must return a list of tuples or set of tuples for identifiers
            # If the device has no identifiers, fallback to connections to avoid the "Invalid device info {'identifiers': set()}" crash
            if device.identifiers:
                return {"identifiers": device.identifiers}
            elif getattr(device, "connections", None):
                return {"connections": device.connections}

        # Fallback if device somehow not found, though we checked in __init__.py
        return {
            "identifiers": {("esphome", self._device_id)},
        }

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        # Check if we should automatically sync the installed version on first fetch
        # (e.g., because the ESP was just flashed, or we're tracking a branch without a commit hash yet).
        if self.coordinator.data:
            is_branch = self._ref in ["main", "master", "dev", "develop", ""]
            latest_version = self.coordinator.data.get("latest_version")

            # If we're tracking a branch, we expect latest_version to be "branch (commit_hash)"
            if is_branch and latest_version and self._installed_version in ["main", "master", "dev", "develop", ""]:
                # The ESP was tracking a raw branch string, update it to the specific commit hash
                self._installed_version = latest_version
                self._stored_data[self._store_key] = self._installed_version
                self.hass.async_create_task(self._store.async_save(self._stored_data))

        return self._installed_version

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_version") # <-- FIX: Nicht latest_commit!
        return None

    @property
    def release_url(self) -> str | None:
        """URL to the full release notes of the latest version available."""
        if self.coordinator.data:
            return self.coordinator.data.get("release_url")
        return None

    @callback
    def async_update_device_sw_version(self, new_sw_version: str) -> None:
        """Update the firmware version to detect reflashes."""
        if self._sw_version != new_sw_version:
            self._sw_version = new_sw_version
            self._stored_data[self._sw_store_key] = new_sw_version

            # If the device was reflashed, we assume it pulled the latest Github code
            # We clear the installed version so it re-syncs seamlessly.
            self._installed_version = None
            if self.coordinator.data:
                self._installed_version = self.coordinator.data.get("latest_version", self._ref)

            if not self._installed_version:
                self._installed_version = self._ref if self._ref else "main"

            self._stored_data[self._store_key] = self._installed_version

            self.hass.async_create_task(self._store.async_save(self._stored_data))
            self.async_write_ha_state()
