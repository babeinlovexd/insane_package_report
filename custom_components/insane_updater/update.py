# https://github.com/babeinlovexd

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
from homeassistant.util import slugify

from .const import COMMON_BRANCH_NAMES, DOMAIN, SIGNAL_NEW_PACKAGE
from .coordinator import GitHubPackageCoordinator
from .utils import parse_github_url

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

        entity_id = f"{device_id}_{slugify(url)}"

        if entity_id in coordinators:
            if coordinators[entity_id] is not None:
                entity = coordinators[entity_id]["entity"]

                # Update ref if changed in the event (e.g. user changed ref in YAML and recompiled)
                if entity._ref != ref:
                    entity._ref = ref
                    coordinators[entity_id]["coordinator"].ref = ref
                    hass.async_create_task(coordinators[entity_id]["coordinator"].async_request_refresh())

                entity.async_update_device_sw_version(sw_version)
            return

        coordinators[entity_id] = None

        coordinator = GitHubPackageCoordinator(
            hass, domain_data["token"], url, ref, pkg_type, domain_data["update_interval"]
        )

        entity = InsanePackageUpdateEntity(
            coordinator, device_id, url, ref, pkg_type, store, stored_data, sw_version
        )

        coordinators[entity_id] = {"coordinator": coordinator, "entity": entity}

        async_add_entities([entity])

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

        url_slug = slugify(self._url)
        self._store_key = f"{self._device_id}_{url_slug}"
        self._sw_store_key = f"sw_{self._device_id}"

        self._installed_version = self._stored_data.get(self._store_key)

        previous_sw_version = self._stored_data.get(self._sw_store_key)

        if previous_sw_version != self._sw_version:
            self._installed_version = None

            self._stored_data[self._sw_store_key] = self._sw_version
            self.coordinator.hass.async_create_task(self._store.async_save(self._stored_data))

        if not self._installed_version:
            self._installed_version = self._ref if self._ref else "main"

        try:
            _, repo_name = parse_github_url(self._url)
        except ValueError:
            repo_name = self._url.split("/")[-1]

        self._attr_unique_id = f"insane_updater_{self._device_id}_{url_slug}"
        self._attr_name = f"{repo_name} Update"

    @property
    def device_info(self):
        """Return device registry information for this entity."""
        registry = dr.async_get(self.hass)
        device = registry.async_get(self._device_id)

        if device:
            if device.identifiers:
                return {"identifiers": device.identifiers}
            elif getattr(device, "connections", None):
                return {"connections": device.connections}

        return {
            "identifiers": {("esphome", self._device_id)},
        }

    @property
    def installed_version(self) -> str | None:
        """Version installed and in use."""
        return self._installed_version

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            is_branch = self._ref in COMMON_BRANCH_NAMES
            latest_version = self.coordinator.data.get("latest_version")

            if is_branch and latest_version and self._installed_version in COMMON_BRANCH_NAMES:
                self._installed_version = latest_version
                self._stored_data[self._store_key] = self._installed_version
                if self.hass:
                    self.hass.async_create_task(self._store.async_save(self._stored_data))

        if self.hass:
            super()._handle_coordinator_update()

    @property
    def latest_version(self) -> str | None:
        """Latest version available for install."""
        if self.coordinator.data:
            return self.coordinator.data.get("latest_version")
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

            is_branch = self._ref in COMMON_BRANCH_NAMES

            if is_branch:
                self._installed_version = self._ref if self._ref else "main"
            else:
                self._installed_version = self._ref

            if not self._installed_version:
                self._installed_version = "main"

            self._stored_data[self._store_key] = self._installed_version

            if self.hass:
                self.hass.async_create_task(self._store.async_save(self._stored_data))
                self.async_write_ha_state()
