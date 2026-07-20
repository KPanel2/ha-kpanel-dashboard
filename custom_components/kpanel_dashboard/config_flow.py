"""Config flow for KPanel Dashboard."""

from __future__ import annotations

import secrets
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_USER_ID,
    CONF_USERNAME,
    DEFAULT_DASHBOARD_PATH,
    DOMAIN,
)
from .kiosk_config import KioskConfig


async def _active_users(hass: HomeAssistant) -> dict[str, str]:
    users = await hass.auth.async_get_users()
    return {
        user.id: (user.name or user.id)
        for user in users
        if user.is_active and not user.system_generated
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for KPanel Dashboard."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending_data: dict[str, Any] | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        users = await _active_users(self.hass)

        if user_input is not None:
            user_id = user_input[CONF_USER_ID]
            if user_id not in users:
                errors[CONF_USER_ID] = "unknown_user"
            else:
                try:
                    dashboard_path = KioskConfig.normalize_dashboard_path(
                        user_input.get(CONF_DASHBOARD_PATH, DEFAULT_DASHBOARD_PATH)
                    )
                except ValueError:
                    errors[CONF_DASHBOARD_PATH] = "invalid_path"
                else:
                    self._pending_data = {
                        CONF_USER_ID: user_id,
                        CONF_USERNAME: users[user_id],
                        CONF_DASHBOARD_PATH: dashboard_path,
                        CONF_BINDING_SECRET: secrets.token_urlsafe(24),
                        CONF_HIDE_HEADER: bool(
                            user_input.get(CONF_HIDE_HEADER, True)
                        ),
                        CONF_HIDE_SIDEBAR: bool(
                            user_input.get(CONF_HIDE_SIDEBAR, True)
                        ),
                    }
                    return await self.async_step_confirm()

        schema = vol.Schema(
            {
                vol.Required(CONF_USER_ID): vol.In(users) if users else str,
                vol.Required(
                    CONF_DASHBOARD_PATH, default=DEFAULT_DASHBOARD_PATH
                ): str,
                vol.Optional(CONF_HIDE_HEADER, default=True): bool,
                vol.Optional(CONF_HIDE_SIDEBAR, default=True): bool,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Show the binding secret once, then create the entry."""
        assert self._pending_data is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._pending_data[CONF_USERNAME],
                data=self._pending_data,
            )

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            description_placeholders={
                "binding_secret": self._pending_data[CONF_BINDING_SECRET],
                "username": self._pending_data[CONF_USERNAME],
                "dashboard_path": self._pending_data[CONF_DASHBOARD_PATH],
            },
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Reveal or rotate the binding secret after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        current_secret = self.config_entry.data.get(CONF_BINDING_SECRET, "")

        if user_input is not None:
            if user_input.get("rotate_binding_secret"):
                new_data = {
                    **self.config_entry.data,
                    CONF_BINDING_SECRET: secrets.token_urlsafe(24),
                }
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_data
                )
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Optional("rotate_binding_secret", default=False): bool}
            ),
            description_placeholders={"binding_secret": current_secret},
        )
