"""Unit tests for AuthTokenService with injected auth doubles."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.kpanel_dashboard.auth_token_service import (
    AuthTokenError,
    AuthTokenService,
)


def _user(user_id: str = "user-1", *, active: bool = True) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.is_active = active
    user.system_generated = False
    return user


def _refresh(
    token_id: str = "rt-1",
    token: str = "refresh-secret",
    *,
    user: MagicMock | None = None,
) -> MagicMock:
    rt = MagicMock()
    rt.id = token_id
    rt.token = token
    rt.access_token_expiration = timedelta(seconds=1800)
    rt.client_id = "https://ha.example/"
    rt.user = user or _user()
    return rt


def _hass_with_auth() -> MagicMock:
    hass = MagicMock()
    hass.auth.async_get_user = AsyncMock()
    hass.auth.async_create_refresh_token = AsyncMock()
    hass.auth.async_get_refresh_token = MagicMock()
    hass.auth.async_remove_refresh_token = MagicMock()
    hass.auth.async_create_access_token = MagicMock(return_value="access-jwt")
    return hass


@pytest.mark.asyncio
async def test_mint_creates_refresh_when_missing() -> None:
    hass = _hass_with_auth()
    user = _user()
    refresh = _refresh()
    hass.auth.async_get_user.return_value = user
    hass.auth.async_get_refresh_token.return_value = None
    hass.auth.async_create_refresh_token.return_value = refresh

    service = AuthTokenService(hass)
    tokens, token_id = await service.mint_hass_tokens(
        user_id="user-1",
        hass_url="https://ha.example",
        existing_token_id=None,
        now_ms=1_700_000_000_000,
    )

    assert token_id == "rt-1"
    assert tokens["access_token"] == "access-jwt"
    assert tokens["refresh_token"] == "refresh-secret"
    assert tokens["expires_in"] == 1800
    hass.auth.async_create_refresh_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_mint_reuses_existing_refresh_token() -> None:
    hass = _hass_with_auth()
    user = _user()
    refresh = _refresh(user=user)
    hass.auth.async_get_user.return_value = user
    hass.auth.async_get_refresh_token.return_value = refresh

    service = AuthTokenService(hass)
    tokens, token_id = await service.mint_hass_tokens(
        user_id="user-1",
        hass_url="https://ha.example",
        existing_token_id="rt-1",
        now_ms=1_700_000_000_000,
    )

    assert token_id == "rt-1"
    assert tokens["refresh_token"] == "refresh-secret"
    hass.auth.async_create_refresh_token.assert_not_called()


@pytest.mark.asyncio
async def test_mint_remints_when_existing_client_id_mismatches() -> None:
    hass = _hass_with_auth()
    user = _user()
    stale = _refresh(user=user)
    stale.client_id = "https://other.example/"
    fresh = _refresh("rt-2", "new-secret", user=user)
    hass.auth.async_get_user.return_value = user
    hass.auth.async_get_refresh_token.return_value = stale
    hass.auth.async_create_refresh_token.return_value = fresh

    service = AuthTokenService(hass)
    tokens, token_id = await service.mint_hass_tokens(
        user_id="user-1",
        hass_url="https://ha.example",
        existing_token_id="rt-1",
        now_ms=0,
    )
    assert token_id == "rt-2"
    assert tokens["refresh_token"] == "new-secret"
    hass.auth.async_create_refresh_token.assert_awaited_once()

    hass = _hass_with_auth()
    hass.auth.async_get_user.return_value = None
    service = AuthTokenService(hass)
    with pytest.raises(AuthTokenError, match="user"):
        await service.mint_hass_tokens(
            user_id="missing",
            hass_url="https://ha.example",
        )


@pytest.mark.asyncio
async def test_rotate_revokes_previous_token() -> None:
    hass = _hass_with_auth()
    user = _user()
    old = _refresh("rt-old", "old-secret", user=user)
    new = _refresh("rt-new", "new-secret", user=user)
    hass.auth.async_get_user.return_value = user
    hass.auth.async_get_refresh_token.return_value = old
    hass.auth.async_create_refresh_token.return_value = new

    service = AuthTokenService(hass)
    tokens, token_id = await service.rotate_tokens(
        user_id="user-1",
        hass_url="https://ha.example",
        existing_token_id="rt-old",
        now_ms=1_700_000_000_000,
    )

    hass.auth.async_remove_refresh_token.assert_called_once_with(old)
    assert token_id == "rt-new"
    assert tokens["refresh_token"] == "new-secret"
