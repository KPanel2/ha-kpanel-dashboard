"""Tests for KioskConfig pure domain model."""

import pytest

from custom_components.kpanel_dashboard.kiosk_config import KioskConfig


def test_from_mapping_requires_user_id() -> None:
    with pytest.raises(ValueError, match="user_id"):
        KioskConfig.from_mapping(
            {
                "dashboard_path": "/lovelace/kiosk",
                "binding_secret": "secret",
            }
        )


def test_from_mapping_defaults() -> None:
    cfg = KioskConfig.from_mapping({"user_id": "abc-123"})
    assert cfg.user_id == "abc-123"
    assert cfg.username is None
    assert cfg.dashboard_path == "/lovelace/kiosk"
    assert cfg.binding_secret is None
    assert cfg.hide_header is True
    assert cfg.hide_sidebar is True


def test_from_mapping_preserves_fields() -> None:
    cfg = KioskConfig.from_mapping(
        {
            "user_id": "u1",
            "username": "kiosk",
            "dashboard_path": "/lovelace/panel",
            "binding_secret": "s3cret",
            "hide_header": False,
            "hide_sidebar": False,
        }
    )
    assert cfg.user_id == "u1"
    assert cfg.username == "kiosk"
    assert cfg.dashboard_path == "/lovelace/panel"
    assert cfg.binding_secret == "s3cret"
    assert cfg.hide_header is False
    assert cfg.hide_sidebar is False


def test_to_entry_data_round_trip() -> None:
    cfg = KioskConfig(
        user_id="u1",
        username="kiosk",
        dashboard_path="/lovelace/kiosk",
        binding_secret="secret",
        hide_header=True,
        hide_sidebar=True,
    )
    restored = KioskConfig.from_mapping(cfg.to_entry_data())
    assert restored == cfg


def test_normalize_dashboard_path_adds_leading_slash() -> None:
    assert KioskConfig.normalize_dashboard_path("lovelace/kiosk") == "/lovelace/kiosk"


def test_normalize_dashboard_path_rejects_empty() -> None:
    with pytest.raises(ValueError, match="dashboard_path"):
        KioskConfig.normalize_dashboard_path("   ")
