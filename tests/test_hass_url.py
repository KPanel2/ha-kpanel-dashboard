"""Tests for hass base URL resolution (LAN vs public)."""

from types import SimpleNamespace

from custom_components.kpanel_dashboard.const import CONF_LOCAL_HASS_URL
from custom_components.kpanel_dashboard.hass_url import (
    normalize_hass_base_url,
    resolve_hass_base_url,
)


def test_normalize_hass_base_url_strips_slash() -> None:
    assert (
        normalize_hass_base_url("http://172.16.24.1:8123/")
        == "http://172.16.24.1:8123"
    )


def test_normalize_hass_base_url_rejects_relative() -> None:
    try:
        normalize_hass_base_url("/control-panel")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_resolve_prefers_local_override() -> None:
    hass = SimpleNamespace(
        config=SimpleNamespace(
            internal_url="http://192.168.1.1:8123",
            external_url="https://homeassistant.example",
        )
    )
    assert (
        resolve_hass_base_url(
            hass,
            entry_data={CONF_LOCAL_HASS_URL: "http://172.16.24.1:8123"},
        )
        == "http://172.16.24.1:8123"
    )


def test_resolve_prefers_internal_over_external() -> None:
    hass = SimpleNamespace(
        config=SimpleNamespace(
            internal_url="http://172.16.24.1:8123",
            external_url="https://homeassistant.example",
        )
    )
    assert resolve_hass_base_url(hass) == "http://172.16.24.1:8123"


def test_resolve_falls_back_to_external_then_origin() -> None:
    hass = SimpleNamespace(
        config=SimpleNamespace(internal_url=None, external_url="https://ha.example")
    )
    assert resolve_hass_base_url(hass) == "https://ha.example"

    hass2 = SimpleNamespace(config=SimpleNamespace(internal_url=None, external_url=None))
    assert (
        resolve_hass_base_url(hass2, request_origin="http://172.16.24.1:8123")
        == "http://172.16.24.1:8123"
    )
