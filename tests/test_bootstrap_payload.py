"""Tests for empty bootstrap payload builder (phase 2 stub)."""

from custom_components.kpanel_dashboard.bootstrap import build_empty_bootstrap_payload
from custom_components.kpanel_dashboard.kiosk_config import KioskConfig


def test_empty_bootstrap_payload_schema() -> None:
    cfg = KioskConfig(
        user_id="u1",
        username="kiosk",
        dashboard_path="/lovelace/kiosk",
        binding_secret="secret",
        hide_header=True,
        hide_sidebar=True,
    )
    payload = build_empty_bootstrap_payload(
        cfg,
        hass_url="https://ha.example",
    )
    assert payload == {
        "hass_url": "https://ha.example",
        "hass_tokens": None,
        "dashboard_url": "https://ha.example/lovelace/kiosk",
        "kiosk": {
            "hide_header": True,
            "hide_sidebar": True,
        },
        "ready": False,
    }


def test_empty_bootstrap_joins_hass_url_and_path() -> None:
    cfg = KioskConfig.from_mapping(
        {"user_id": "u1", "dashboard_path": "/lovelace/panel"}
    )
    payload = build_empty_bootstrap_payload(cfg, hass_url="https://ha.example/")
    assert payload["dashboard_url"] == "https://ha.example/lovelace/panel"
