"""Tests for frontend kiosk JS registration."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kpanel_dashboard.const import (
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_USER_ID,
    CONF_USERNAME,
    DOMAIN,
)
from custom_components.kpanel_dashboard.frontend import (
    KIOSK_JS_FILE,
    KIOSK_JS_URL,
    async_register_frontend,
)


def test_kiosk_js_bundle_exists() -> None:
    assert KIOSK_JS_FILE.is_file()
    assert KIOSK_JS_FILE.suffix == ".js"


@pytest.mark.asyncio
async def test_async_register_frontend_defers_js_until_frontend() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http = MagicMock(spec=["register_static_path", "register_view"])

    with patch(
        "custom_components.kpanel_dashboard.frontend.async_when_setup"
    ) as when_setup, patch(
        "custom_components.kpanel_dashboard.frontend.add_extra_js_url"
    ) as add_js:
        await async_register_frontend(hass)
        await async_register_frontend(hass)  # idempotent

    hass.http.register_static_path.assert_called_once_with(
        KIOSK_JS_URL, str(KIOSK_JS_FILE), True
    )
    when_setup.assert_called_once()
    add_js.assert_not_called()
    assert hass.data[DOMAIN]["_frontend_registered"] is True


@pytest.mark.asyncio
async def test_async_register_frontend_adds_js_when_frontend_ready() -> None:
    hass = MagicMock()
    hass.data = {DATA_EXTRA_MODULE_URL: set()}
    hass.http = MagicMock(spec=["register_static_path", "register_view"])

    with patch(
        "custom_components.kpanel_dashboard.frontend.add_extra_js_url"
    ) as add_js:
        await async_register_frontend(hass)

    add_js.assert_called_once_with(hass, KIOSK_JS_URL)


@pytest.mark.asyncio
async def test_async_register_frontend_skips_missing_bundle() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http = MagicMock(spec=["register_static_path"])
    with patch(
        "custom_components.kpanel_dashboard.frontend.KIOSK_JS_FILE"
    ) as missing:
        missing.is_file.return_value = False
        await async_register_frontend(hass)
    hass.http.register_static_path.assert_not_called()
    assert DOMAIN not in hass.data or not hass.data[DOMAIN].get(
        "_frontend_registered"
    )


async def test_setup_serves_kiosk_js(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    hass.config.external_url = "https://ha.example"
    user = await hass.auth.async_create_user("Kiosk User")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk",
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

    assert hass.data[DOMAIN].get("_frontend_registered") is True
    client = await hass_client()
    resp = await client.get(KIOSK_JS_URL)
    assert resp.status == 200
    body = await resp.text()
    assert "KPanelKiosk" in body
