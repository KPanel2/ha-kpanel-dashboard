"""Config flow tests for kpanel_dashboard."""

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
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


def _mock_user() -> MagicMock:
    mock_user = MagicMock()
    mock_user.id = "user-1"
    mock_user.name = "Kiosk User"
    mock_user.is_active = True
    mock_user.system_generated = False
    return mock_user


async def test_user_step_form(hass: HomeAssistant, enable_custom_integrations) -> None:
    """Config flow shows user form with user + dashboard fields."""
    with patch(
        "homeassistant.auth.AuthManager.async_get_users",
        new=AsyncMock(return_value=[_mock_user()]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_shows_binding_secret_before_create(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Valid user step advances to confirm step that reveals the binding secret."""
    with patch(
        "homeassistant.auth.AuthManager.async_get_users",
        new=AsyncMock(return_value=[_mock_user()]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USER_ID: "user-1",
                CONF_DASHBOARD_PATH: "/lovelace/kiosk",
                CONF_HIDE_HEADER: True,
                CONF_HIDE_SIDEBAR: True,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "confirm"
    secret = result2["description_placeholders"]["binding_secret"]
    assert isinstance(secret, str)
    assert len(secret) >= 16


async def test_confirm_step_creates_entry(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Confirming after secret reveal creates the config entry."""
    with patch(
        "homeassistant.auth.AuthManager.async_get_users",
        new=AsyncMock(return_value=[_mock_user()]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USER_ID: "user-1",
                CONF_DASHBOARD_PATH: "/lovelace/kiosk",
                CONF_HIDE_HEADER: True,
                CONF_HIDE_SIDEBAR: True,
            },
        )
        secret = result2["description_placeholders"]["binding_secret"]

        with patch(
            "custom_components.kpanel_dashboard.async_setup_entry",
            return_value=True,
        ):
            result3 = await hass.config_entries.flow.async_configure(
                result2["flow_id"], {}
            )
            await hass.async_block_till_done()

    assert result3["type"] == FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Kiosk User"
    assert result3["data"][CONF_USER_ID] == "user-1"
    assert result3["data"][CONF_USERNAME] == "Kiosk User"
    assert result3["data"][CONF_DASHBOARD_PATH] == "/lovelace/kiosk"
    assert result3["data"][CONF_BINDING_SECRET] == secret
    assert result3["data"][CONF_HIDE_HEADER] is True
    assert result3["data"][CONF_HIDE_SIDEBAR] is True


async def test_user_step_unknown_user(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """User removed between form show and submit returns form error."""
    mock_user = _mock_user()

    with patch(
        "homeassistant.auth.AuthManager.async_get_users",
        new=AsyncMock(side_effect=[[mock_user], []]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USER_ID: "user-1",
                CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"user_id": "unknown_user"}


async def test_user_step_invalid_dashboard_path(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Blank dashboard path returns form error."""
    with patch(
        "homeassistant.auth.AuthManager.async_get_users",
        new=AsyncMock(return_value=[_mock_user()]),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USER_ID: "user-1",
                CONF_DASHBOARD_PATH: "   ",
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"dashboard_path": "invalid_path"}


async def test_options_flow_shows_and_rotates_binding_secret(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    """Options flow reveals current secret and shows the new one after rotate."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={
            CONF_USER_ID: "user-1",
            CONF_USERNAME: "Kiosk User",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "old-secret-value-123456",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert (
        result["description_placeholders"]["binding_secret"]
        == "old-secret-value-123456"
    )
    assert result["data_schema"].schema  # includes display field

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"rotate_binding_secret": True, "binding_secret_display": "ignored"},
    )
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "show_secret"
    new_secret = result2["description_placeholders"]["binding_secret"]
    assert new_secret != "old-secret-value-123456"
    assert len(new_secret) >= 16
    assert entry.data[CONF_BINDING_SECRET] == new_secret

    result3 = await hass.config_entries.options.async_configure(
        result2["flow_id"],
        {"binding_secret_display": new_secret},
    )
    assert result3["type"] == FlowResultType.CREATE_ENTRY


async def test_options_flow_keeps_secret_without_rotate(
    hass: HomeAssistant, enable_custom_integrations
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={
            CONF_USER_ID: "user-1",
            CONF_USERNAME: "Kiosk User",
            CONF_DASHBOARD_PATH: "/lovelace/kiosk",
            CONF_BINDING_SECRET: "keep-me-secret-abcdef",
            CONF_HIDE_HEADER: True,
            CONF_HIDE_SIDEBAR: True,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "rotate_binding_secret": False,
            "binding_secret_display": "keep-me-secret-abcdef",
            "local_hass_url": "http://172.16.24.1:8123",
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_BINDING_SECRET] == "keep-me-secret-abcdef"
    assert entry.data["local_hass_url"] == "http://172.16.24.1:8123"


def test_options_flow_handler_does_not_assign_config_entry_property() -> None:
    """HA 2025.12+ makes OptionsFlow.config_entry read-only; constructing must not set it."""
    from custom_components.kpanel_dashboard.config_flow import OptionsFlowHandler

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kiosk User",
        data={CONF_BINDING_SECRET: "secret-value"},
    )
    handler = OptionsFlowHandler(entry)
    assert handler.config_entry is entry
    assert handler._config_entry is entry
