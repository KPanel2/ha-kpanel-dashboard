"""KPanel Dashboard Home Assistant integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .auth_token_service import AuthTokenError, AuthTokenService
from .bootstrap import async_register_bootstrap_view
from .const import (
    BOOTSTRAP_RATE_LIMIT_MAX,
    BOOTSTRAP_RATE_LIMIT_WINDOW_SECONDS,
    CONF_REFRESH_TOKEN_ID,
    DOMAIN,
    SERVICE_ROTATE_TOKENS,
)
from .frontend import async_register_frontend
from .kiosk_config import KioskConfig
from .rate_limit import BootstrapRateLimiter

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = []


def _hass_base_url(hass: HomeAssistant) -> str:
    return str(hass.config.external_url or hass.config.internal_url or "").rstrip(
        "/"
    )


async def _ensure_entry_tokens(
    hass: HomeAssistant, entry: ConfigEntry, token_service: AuthTokenService
) -> None:
    config = KioskConfig.from_mapping(entry.data)
    hass_url = _hass_base_url(hass) or "http://homeassistant.local:8123"
    try:
        _tokens, refresh_token_id = await token_service.mint_hass_tokens(
            user_id=config.user_id,
            hass_url=hass_url,
            existing_token_id=config.refresh_token_id,
        )
    except AuthTokenError as err:
        raise HomeAssistantError(f"Unable to mint KPanel tokens: {err}") from err

    if entry.data.get(CONF_REFRESH_TOKEN_ID) != refresh_token_id:
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_REFRESH_TOKEN_ID: refresh_token_id},
        )


async def async_setup(hass: HomeAssistant, _config: dict[str, Any]) -> bool:
    """Set up the integration (YAML not supported; config entries only)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up KPanel Dashboard from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    token_service = AuthTokenService(hass)
    hass.data[DOMAIN]["token_service"] = token_service
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await _ensure_entry_tokens(hass, entry, token_service)

    if not hass.data[DOMAIN].get("_bootstrap_registered"):
        limiter = BootstrapRateLimiter(
            max_calls=BOOTSTRAP_RATE_LIMIT_MAX,
            window_seconds=BOOTSTRAP_RATE_LIMIT_WINDOW_SECONDS,
        )
        async_register_bootstrap_view(hass, token_service, rate_limiter=limiter)
        hass.data[DOMAIN]["_bootstrap_registered"] = True
        hass.data[DOMAIN]["rate_limiter"] = limiter
        _LOGGER.debug("Registered KPanel bootstrap view")

    await async_register_frontend(hass)

    if not hass.data[DOMAIN].get("_services_registered"):
        await _async_register_services(hass)
        hass.data[DOMAIN]["_services_registered"] = True

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_register_services(hass: HomeAssistant) -> None:
    async def handle_rotate_tokens(_call: ServiceCall) -> None:
        token_service: AuthTokenService = hass.data[DOMAIN]["token_service"]
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise HomeAssistantError("KPanel Dashboard is not configured")
        entry = entries[0]
        config = KioskConfig.from_mapping(entry.data)
        hass_url = _hass_base_url(hass) or "http://homeassistant.local:8123"
        try:
            _tokens, refresh_token_id = await token_service.rotate_tokens(
                user_id=config.user_id,
                hass_url=hass_url,
                existing_token_id=config.refresh_token_id,
            )
        except AuthTokenError as err:
            raise HomeAssistantError(str(err)) from err
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_REFRESH_TOKEN_ID: refresh_token_id},
        )
        _LOGGER.info("Rotated KPanel tokens for user %s", config.user_id)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ROTATE_TOKENS,
        handle_rotate_tokens,
        schema=vol.Schema({}),
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
