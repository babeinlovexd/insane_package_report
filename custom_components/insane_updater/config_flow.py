from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries, core
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers import selector

from .const import CONF_GITHUB_TOKEN, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL, DOMAIN

UPDATE_INTERVAL_OPTIONS = [
    selector.SelectOptionDict(value="1", label="1h"),
    selector.SelectOptionDict(value="3", label="3h"),
    selector.SelectOptionDict(value="6", label="6h"),
    selector.SelectOptionDict(value="12", label="12h"),
    selector.SelectOptionDict(value="24", label="24h"),
]

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_GITHUB_TOKEN, default=""): str,
        vol.Optional(CONF_UPDATE_INTERVAL, default=str(DEFAULT_UPDATE_INTERVAL)): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=UPDATE_INTERVAL_OPTIONS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Insane Updater."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Insane Updater", data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA
        )

    @staticmethod
    @core.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Insane Updater."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_GITHUB_TOKEN,
                        default=self.config_entry.options.get(
                            CONF_GITHUB_TOKEN,
                            self.config_entry.data.get(CONF_GITHUB_TOKEN, ""),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL,
                            self.config_entry.data.get(
                                CONF_UPDATE_INTERVAL, str(DEFAULT_UPDATE_INTERVAL)
                            ),
                        ),
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=UPDATE_INTERVAL_OPTIONS,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
        )
