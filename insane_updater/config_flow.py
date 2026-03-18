"""Config flow for Insane Updater integration."""
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_GITHUB_TOKEN

class InsaneUpdaterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Insane Updater."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # We don't strictly validate the token, we just save it.
            return self.async_create_entry(title="Insane Updater", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(CONF_GITHUB_TOKEN, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
