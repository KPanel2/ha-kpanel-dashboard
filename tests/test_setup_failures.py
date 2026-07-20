"""Coverage for setup/rotate failure paths."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kpanel_dashboard.auth_token_service import AuthTokenError
from custom_components.kpanel_dashboard.const import (
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_REFRESH_TOKEN_ID,
    CONF_USER_ID,
    CONF_USERNAME,
    DOMAIN,
    SERVICE_ROTATE_TOKENS,
)


async def test_setup_fails_when_user_missing(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    hass.config.external_url = "https://ha.example"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Missing",
        data={
            CONF_USER_ID: "does-not-exist",
            CONF_USERNAME: "Missing",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "secret",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)


async def test_rotate_service_propagates_auth_error(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    hass.config.external_url = "https://ha.example"
    user = await hass.auth.async_create_user("Kiosk User")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={
            CONF_USER_ID: user.id,
            CONF_USERNAME: "Kiosk User",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "secret",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with patch(
        "custom_components.kpanel_dashboard.auth_token_service.AuthTokenService.rotate_tokens",
        new=AsyncMock(side_effect=AuthTokenError("boom")),
    ):
        with pytest.raises(HomeAssistantError, match="boom"):
            await hass.services.async_call(
                DOMAIN, SERVICE_ROTATE_TOKENS, {}, blocking=True
            )


async def test_bootstrap_persists_new_refresh_token_id(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    """If mint returns a new refresh token id, entry data is updated."""
    from custom_components.kpanel_dashboard.const import (
        BINDING_SECRET_HEADER,
        BOOTSTRAP_PATH,
    )

    hass.config.external_url = "https://ha.example"
    user = await hass.auth.async_create_user("Kiosk User")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={
            CONF_USER_ID: user.id,
            CONF_USERNAME: "Kiosk User",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "secret",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    client = await hass_client()
    with patch(
        "custom_components.kpanel_dashboard.auth_token_service.AuthTokenService.mint_hass_tokens",
        new=AsyncMock(
            return_value=(
                {
                    "hassUrl": "https://ha.example",
                    "clientId": "https://ha.example/",
                    "access_token": "a",
                    "refresh_token": "r",
                    "token_type": "Bearer",
                    "expires_in": 1800,
                    "expires": 1,
                },
                "brand-new-token-id",
            )
        ),
    ):
        resp = await client.get(
            BOOTSTRAP_PATH, headers={BINDING_SECRET_HEADER: "secret"}
        )
    assert resp.status == 200
    assert entry.data[CONF_REFRESH_TOKEN_ID] == "brand-new-token-id"
