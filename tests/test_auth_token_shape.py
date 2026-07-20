"""Tests for hassTokens payload shaping and client_id derivation."""

from custom_components.kpanel_dashboard.auth_token_service import (
    build_hass_tokens,
    derive_client_id,
)


def test_derive_client_id_adds_trailing_slash() -> None:
    assert derive_client_id("https://ha.example") == "https://ha.example/"
    assert derive_client_id("https://ha.example/") == "https://ha.example/"


def test_build_hass_tokens_shape() -> None:
    tokens = build_hass_tokens(
        hass_url="https://ha.example",
        client_id="https://ha.example/",
        access_token="access",
        refresh_token="refresh",
        expires_in=1800,
        now_ms=1_000_000_000_000,
    )
    assert tokens == {
        "hassUrl": "https://ha.example",
        "clientId": "https://ha.example/",
        "access_token": "access",
        "refresh_token": "refresh",
        "token_type": "Bearer",
        "expires_in": 1800,
        "expires": 1_000_000_000_000 + 1800 * 1000,
    }
