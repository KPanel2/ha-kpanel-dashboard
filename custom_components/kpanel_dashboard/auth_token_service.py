"""Auth token minting for KPanel hassTokens bootstrap."""

from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant

from .const import CLIENT_NAME

_LOGGER = logging.getLogger(__name__)


class AuthTokenError(Exception):
    """Raised when tokens cannot be minted for the configured user."""


def derive_client_id(hass_url: str) -> str:
    """Stable OAuth-style client_id derived from the HA base URL."""
    return f"{hass_url.rstrip('/')}/"


def build_hass_tokens(
    *,
    hass_url: str,
    client_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    now_ms: int,
) -> dict[str, Any]:
    """Shape tokens for localStorage.hassTokens consumption."""
    return {
        "hassUrl": hass_url.rstrip("/"),
        "clientId": client_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "expires": now_ms + expires_in * 1000,
    }


class AuthTokenService:
    """Mint and rotate HA refresh/access tokens for a kiosk user."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def _get_active_user(self, user_id: str):
        user = await self._hass.auth.async_get_user(user_id)
        if user is None or not user.is_active:
            raise AuthTokenError("user not found or inactive")
        return user

    async def ensure_refresh_token(
        self,
        *,
        user_id: str,
        hass_url: str,
        existing_token_id: str | None = None,
    ):
        """Return an existing valid refresh token or create a new one."""
        user = await self._get_active_user(user_id)
        client_id = derive_client_id(hass_url)

        if existing_token_id:
            existing = self._hass.auth.async_get_refresh_token(existing_token_id)
            if (
                existing is not None
                and existing.user.id == user.id
                and existing.client_id == client_id
            ):
                return existing

        refresh = await self._hass.auth.async_create_refresh_token(
            user,
            client_id=client_id,
            client_name=CLIENT_NAME,
        )
        _LOGGER.info(
            "Created KPanel refresh token %s for user %s", refresh.id, user.id
        )
        return refresh

    async def mint_hass_tokens(
        self,
        *,
        user_id: str,
        hass_url: str,
        existing_token_id: str | None = None,
        now_ms: int | None = None,
        remote_ip: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Return (hassTokens dict, refresh_token_id)."""
        refresh = await self.ensure_refresh_token(
            user_id=user_id,
            hass_url=hass_url,
            existing_token_id=existing_token_id,
        )
        access = self._hass.auth.async_create_access_token(refresh, remote_ip)
        expires_in = int(refresh.access_token_expiration.total_seconds())
        if now_ms is None:
            now_ms = int(time.time() * 1000)
        tokens = build_hass_tokens(
            hass_url=hass_url,
            client_id=derive_client_id(hass_url),
            access_token=access,
            refresh_token=refresh.token,
            expires_in=expires_in,
            now_ms=now_ms,
        )
        return tokens, refresh.id

    async def rotate_tokens(
        self,
        *,
        user_id: str,
        hass_url: str,
        existing_token_id: str | None = None,
        now_ms: int | None = None,
        remote_ip: str | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Revoke the previous refresh token (if any) and mint a new pair."""
        if existing_token_id:
            old = self._hass.auth.async_get_refresh_token(existing_token_id)
            if old is not None:
                self._hass.auth.async_remove_refresh_token(old)
                _LOGGER.info("Revoked KPanel refresh token %s", existing_token_id)

        return await self.mint_hass_tokens(
            user_id=user_id,
            hass_url=hass_url,
            existing_token_id=None,
            now_ms=now_ms,
            remote_ip=remote_ip,
        )
