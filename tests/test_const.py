"""Tests for kpanel_dashboard constants."""

from custom_components.kpanel_dashboard.const import (
    BOOTSTRAP_PATH,
    CONF_BINDING_SECRET,
    CONF_DASHBOARD_PATH,
    CONF_HIDE_HEADER,
    CONF_HIDE_SIDEBAR,
    CONF_USER_ID,
    CONF_USERNAME,
    DEFAULT_DASHBOARD_PATH,
    DOMAIN,
)


def test_domain() -> None:
    assert DOMAIN == "kpanel_dashboard"


def test_bootstrap_path() -> None:
    assert BOOTSTRAP_PATH == "/api/kpanel_dashboard/bootstrap"


def test_default_dashboard_path() -> None:
    assert DEFAULT_DASHBOARD_PATH == "/lovelace/kiosk"


def test_config_keys() -> None:
    assert CONF_USER_ID == "user_id"
    assert CONF_USERNAME == "username"
    assert CONF_DASHBOARD_PATH == "dashboard_path"
    assert CONF_BINDING_SECRET == "binding_secret"
    assert CONF_HIDE_HEADER == "hide_header"
    assert CONF_HIDE_SIDEBAR == "hide_sidebar"
