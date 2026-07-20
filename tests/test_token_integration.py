"""Integration tests: mint tokens on setup and return them from bootstrap."""

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kpanel_dashboard.const import (
    BINDING_SECRET_HEADER,
    BOOTSTRAP_PATH,
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


async def _create_user(hass: HomeAssistant):
    return await hass.auth.async_create_user("Kiosk User")


def _entry(user_id: str, **overrides) -> MockConfigEntry:
    data = {
        CONF_USER_ID: user_id,
        CONF_USERNAME: "Kiosk User",
        CONF_DASHBOARD_PATH: "/lovelace/kiosk",
        CONF_BINDING_SECRET: "test-binding-secret",
        CONF_HIDE_HEADER: True,
        CONF_HIDE_SIDEBAR: True,
    }
    data.update(overrides)
    return MockConfigEntry(domain=DOMAIN, data=data, title="Kiosk User")


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    hass.config.external_url = "https://ha.example"
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_stores_refresh_token_id(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    user = await _create_user(hass)
    entry = _entry(user.id)
    await _setup(hass, entry)

    assert CONF_REFRESH_TOKEN_ID in entry.data
    assert entry.data[CONF_REFRESH_TOKEN_ID]
    stored = hass.auth.async_get_refresh_token(entry.data[CONF_REFRESH_TOKEN_ID])
    assert stored is not None
    assert stored.user.id == user.id


async def test_bootstrap_returns_ready_hass_tokens(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    user = await _create_user(hass)
    entry = _entry(user.id)
    await _setup(hass, entry)

    client = await hass_client()
    resp = await client.get(
        BOOTSTRAP_PATH,
        headers={BINDING_SECRET_HEADER: "test-binding-secret"},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["ready"] is True
    assert body["hass_url"] == "https://ha.example"
    tokens = body["hass_tokens"]
    assert tokens["hassUrl"] == "https://ha.example"
    assert tokens["clientId"] == "https://ha.example/"
    assert tokens["token_type"] == "Bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["expires_in"] == 1800
    assert isinstance(tokens["expires"], int)


async def test_rotate_tokens_service_replaces_refresh_token(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    user = await _create_user(hass)
    entry = _entry(user.id)
    await _setup(hass, entry)
    old_id = entry.data[CONF_REFRESH_TOKEN_ID]

    await hass.services.async_call(
        DOMAIN, SERVICE_ROTATE_TOKENS, {}, blocking=True
    )
    await hass.async_block_till_done()

    new_id = entry.data[CONF_REFRESH_TOKEN_ID]
    assert new_id != old_id
    assert hass.auth.async_get_refresh_token(old_id) is None
    assert hass.auth.async_get_refresh_token(new_id) is not None
