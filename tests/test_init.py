"""Integration setup and bootstrap HTTP auth tests."""

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
    CONF_USER_ID,
    CONF_USERNAME,
    DOMAIN,
)


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


async def _setup_with_http(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    hass.config.external_url = "https://ha.example"
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_entry_registers_bootstrap(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    """Setup registers bootstrap endpoint that returns minted tokens."""
    user = await hass.auth.async_create_user("Kiosk User")
    await _setup_with_http(hass, _entry(user.id))

    client = await hass_client()
    resp = await client.get(
        BOOTSTRAP_PATH,
        headers={BINDING_SECRET_HEADER: "test-binding-secret"},
    )
    assert resp.status == 200
    body = await resp.json()
    assert body["ready"] is True
    assert body["hass_tokens"]["access_token"]
    assert body["dashboard_url"].endswith("/lovelace/kiosk")
    assert body["kiosk"] == {"hide_header": True, "hide_sidebar": True}


async def test_bootstrap_rejects_bad_secret(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    user = await hass.auth.async_create_user("Kiosk User")
    await _setup_with_http(hass, _entry(user.id))

    client = await hass_client()
    resp = await client.get(
        BOOTSTRAP_PATH,
        headers={BINDING_SECRET_HEADER: "wrong"},
    )
    assert resp.status == 401


async def test_bootstrap_rejects_missing_secret(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    user = await hass.auth.async_create_user("Kiosk User")
    await _setup_with_http(hass, _entry(user.id))

    client = await hass_client()
    resp = await client.get(BOOTSTRAP_PATH)
    assert resp.status == 401


async def test_unload_entry(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    user = await hass.auth.async_create_user("Kiosk User")
    entry = _entry(user.id)
    await _setup_with_http(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
