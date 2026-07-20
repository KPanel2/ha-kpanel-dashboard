"""Unit tests for resolve_bootstrap_response (no live HTTP stack)."""

from types import SimpleNamespace

from custom_components.kpanel_dashboard.bootstrap import resolve_bootstrap_response
from custom_components.kpanel_dashboard.const import (
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_USER_ID,
    CONF_USERNAME,
)


def _entry(**overrides) -> SimpleNamespace:
    data = {
        CONF_USER_ID: "user-1",
        CONF_USERNAME: "Kiosk User",
        CONF_DASHBOARD_PATH: "/lovelace/kiosk",
        CONF_BINDING_SECRET: "test-binding-secret",
        CONF_HIDE_HEADER: True,
        CONF_HIDE_SIDEBAR: True,
    }
    data.update(overrides)
    return SimpleNamespace(data=data)


def test_resolve_not_configured() -> None:
    status, body = resolve_bootstrap_response(
        entries=[],
        binding_secret_header="x",
        hass_url="https://ha.example",
    )
    assert status == 404
    assert body == "Integration not configured"


def test_resolve_unauthorized() -> None:
    status, body = resolve_bootstrap_response(
        entries=[_entry()],
        binding_secret_header="wrong",
        hass_url="https://ha.example",
    )
    assert status == 401
    assert body == "Unauthorized"


def test_resolve_missing_secret() -> None:
    status, body = resolve_bootstrap_response(
        entries=[_entry()],
        binding_secret_header=None,
        hass_url="https://ha.example",
    )
    assert status == 401


def test_resolve_bad_entry_data() -> None:
    status, body = resolve_bootstrap_response(
        entries=[_entry(**{CONF_USER_ID: ""})],
        binding_secret_header="test-binding-secret",
        hass_url="https://ha.example",
    )
    assert status == 500
    assert "user_id" in str(body)


def test_resolve_ready_false_payload() -> None:
    status, body = resolve_bootstrap_response(
        entries=[_entry()],
        binding_secret_header="test-binding-secret",
        hass_url="https://ha.example",
    )
    assert status == 200
    assert isinstance(body, dict)
    assert body["ready"] is False
    assert body["hass_tokens"] is None
    assert body["dashboard_url"] == "https://ha.example/lovelace/kiosk"
