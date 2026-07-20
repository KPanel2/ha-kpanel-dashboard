"""Unit tests for AuthTokenError edge paths and inactive users."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.kpanel_dashboard.auth_token_service import (
    AuthTokenError,
    AuthTokenService,
)


@pytest.mark.asyncio
async def test_inactive_user_raises() -> None:
    hass = MagicMock()
    user = MagicMock()
    user.id = "u1"
    user.is_active = False
    hass.auth.async_get_user = AsyncMock(return_value=user)
    service = AuthTokenService(hass)
    with pytest.raises(AuthTokenError, match="inactive"):
        await service.mint_hass_tokens(user_id="u1", hass_url="https://ha.example")


@pytest.mark.asyncio
async def test_rotate_without_existing_still_mints() -> None:
    hass = MagicMock()
    user = MagicMock()
    user.id = "u1"
    user.is_active = True
    refresh = MagicMock()
    refresh.id = "rt-1"
    refresh.token = "secret"
    refresh.access_token_expiration = timedelta(seconds=1800)
    refresh.client_id = "https://ha.example/"
    refresh.user = user
    hass.auth.async_get_user = AsyncMock(return_value=user)
    hass.auth.async_get_refresh_token = MagicMock(return_value=None)
    hass.auth.async_create_refresh_token = AsyncMock(return_value=refresh)
    hass.auth.async_create_access_token = MagicMock(return_value="jwt")
    hass.auth.async_remove_refresh_token = MagicMock()

    service = AuthTokenService(hass)
    tokens, token_id = await service.rotate_tokens(
        user_id="u1",
        hass_url="https://ha.example",
        existing_token_id=None,
        now_ms=0,
    )
    hass.auth.async_remove_refresh_token.assert_not_called()
    assert token_id == "rt-1"
    assert tokens["access_token"] == "jwt"
