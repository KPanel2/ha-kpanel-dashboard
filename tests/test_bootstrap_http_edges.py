"""HTTP edge cases for bootstrap (rate limit + mint failure)."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kpanel_dashboard.auth_token_service import (
    AuthTokenError,
    AuthTokenService,
)
from custom_components.kpanel_dashboard.bootstrap import KPanelBootstrapView
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
from custom_components.kpanel_dashboard.rate_limit import BootstrapRateLimiter


async def _setup_entry(hass: HomeAssistant) -> None:
    hass.config.external_url = "https://ha.example"
    user = await hass.auth.async_create_user("Kiosk User")
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={
            CONF_USER_ID: user.id,
            CONF_USERNAME: "Kiosk User",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "test-binding-secret",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    assert await async_setup_component(hass, "http", {})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_bootstrap_token_mint_failure(
    hass: HomeAssistant, enable_custom_integrations, hass_client
) -> None:
    await _setup_entry(hass)
    client = await hass_client()
    with patch(
        "custom_components.kpanel_dashboard.auth_token_service.AuthTokenService.mint_hass_tokens",
        new=AsyncMock(side_effect=AuthTokenError("user not found or inactive")),
    ):
        resp = await client.get(
            BOOTSTRAP_PATH,
            headers={BINDING_SECRET_HEADER: "test-binding-secret"},
        )
    assert resp.status == 503


async def test_view_returns_429_when_rate_limited() -> None:
    """Unit-level: rate-limited limiter yields HTTP 429."""
    hass = MagicMock()
    entry = MagicMock()
    entry.data = {
        CONF_USER_ID: "u1",
        CONF_USERNAME: "Kiosk",
        CONF_DASHBOARD_PATH: "/lovelace/kiosk",
        CONF_BINDING_SECRET: "secret",
        CONF_HIDE_HEADER: True,
        CONF_HIDE_SIDEBAR: True,
    }
    hass.config_entries.async_entries = MagicMock(return_value=[entry])
    hass.config.external_url = "https://ha.example"
    hass.config.internal_url = None

    limiter = BootstrapRateLimiter(
        max_calls=1, window_seconds=60.0, time_fn=lambda: 1.0
    )
    assert limiter.allow("secret") is True
    assert limiter.allow("secret") is False

    view = KPanelBootstrapView(hass, AuthTokenService(hass), rate_limiter=limiter)
    request = MagicMock(spec=web.Request)
    request.headers = {BINDING_SECRET_HEADER: "secret"}
    request.remote = "127.0.0.1"
    request.url.origin.return_value = "https://ha.example"

    with patch.object(
        view,
        "json_message",
        side_effect=lambda msg, status_code: (status_code, msg),
    ) as mocked:
        result = await view.get(request)

    assert result == (429, "Rate limit exceeded")
    mocked.assert_called_once()
