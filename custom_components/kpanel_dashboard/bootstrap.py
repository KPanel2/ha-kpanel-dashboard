"""Bootstrap HTTP API for KPanel clients."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .auth_token_service import AuthTokenError, AuthTokenService
from .bootstrap_auth import BootstrapAuthError, validate_binding_secret
from .const import (
    BINDING_SECRET_HEADER,
    BOOTSTRAP_PATH,
    BOOTSTRAP_RATE_LIMIT_MAX,
    BOOTSTRAP_RATE_LIMIT_WINDOW_SECONDS,
    CONF_REFRESH_TOKEN_ID,
    DOMAIN,
)
from .kiosk_config import KioskConfig
from .rate_limit import BootstrapRateLimiter

_LOGGER = logging.getLogger(__name__)


def _join_url(base: str, path: str) -> str:
    return f"{base.rstrip('/')}{path}"


def build_bootstrap_payload(
    config: KioskConfig,
    *,
    hass_url: str,
    hass_tokens: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build bootstrap response; ready when hass_tokens are present."""
    return {
        "hass_url": hass_url.rstrip("/"),
        "hass_tokens": hass_tokens,
        "dashboard_url": _join_url(hass_url, config.dashboard_path),
        "kiosk": {
            "hide_header": config.hide_header,
            "hide_sidebar": config.hide_sidebar,
        },
        "ready": hass_tokens is not None,
    }


# Back-compat alias used by earlier phase-2 tests/docs.
def build_empty_bootstrap_payload(
    config: KioskConfig, *, hass_url: str
) -> dict[str, Any]:
    return build_bootstrap_payload(config, hass_url=hass_url, hass_tokens=None)


def authorize_bootstrap(
    *,
    entries: list[Any],
    binding_secret_header: str | None,
) -> tuple[int, KioskConfig | str]:
    """
    Validate binding secret and load kiosk config.

    Returns (status_code, KioskConfig) on success or (status, message) on error.
    """
    if not entries:
        return 404, "Integration not configured"

    entry = entries[0]
    try:
        config = KioskConfig.from_mapping(entry.data)
    except ValueError as err:
        return 500, str(err)

    try:
        validate_binding_secret(
            provided=binding_secret_header, expected=config.binding_secret
        )
    except BootstrapAuthError:
        return 401, "Unauthorized"

    return 200, config


# Deprecated name kept for existing unit tests during transition.
def resolve_bootstrap_response(
    *,
    entries: list[Any],
    binding_secret_header: str | None,
    hass_url: str,
) -> tuple[int, dict[str, Any] | str]:
    status, result = authorize_bootstrap(
        entries=entries, binding_secret_header=binding_secret_header
    )
    if not isinstance(result, KioskConfig):
        return status, result
    return 200, build_empty_bootstrap_payload(result, hass_url=hass_url)


class KPanelBootstrapView(HomeAssistantView):
    """Authenticated bootstrap endpoint for KPanel clients."""

    url = BOOTSTRAP_PATH
    name = "api:kpanel_dashboard:bootstrap"
    requires_auth = False

    def __init__(
        self,
        hass: HomeAssistant,
        token_service: AuthTokenService,
        rate_limiter: BootstrapRateLimiter | None = None,
    ) -> None:
        self._hass = hass
        self._tokens = token_service
        self._limiter = rate_limiter or BootstrapRateLimiter(
            max_calls=BOOTSTRAP_RATE_LIMIT_MAX,
            window_seconds=BOOTSTRAP_RATE_LIMIT_WINDOW_SECONDS,
        )

    async def get(self, request: web.Request) -> web.Response:
        entries = list(self._hass.config_entries.async_entries(DOMAIN))
        provided = request.headers.get(BINDING_SECRET_HEADER)
        status, result = authorize_bootstrap(
            entries=entries, binding_secret_header=provided
        )
        if not isinstance(result, KioskConfig):
            return self.json_message(result, status_code=status)

        limit_key = result.binding_secret or "anonymous"
        if not self._limiter.allow(limit_key):
            _LOGGER.warning("Bootstrap rate limit exceeded")
            return self.json_message("Rate limit exceeded", status_code=429)

        hass_url = str(
            self._hass.config.external_url
            or self._hass.config.internal_url
            or request.url.origin()
        )
        entry = entries[0]
        try:
            hass_tokens, refresh_token_id = await self._tokens.mint_hass_tokens(
                user_id=result.user_id,
                hass_url=hass_url,
                existing_token_id=entry.data.get(CONF_REFRESH_TOKEN_ID),
                remote_ip=request.remote,
            )
        except AuthTokenError as err:
            _LOGGER.error("Bootstrap token mint failed: %s", err)
            return self.json_message(str(err), status_code=503)

        if entry.data.get(CONF_REFRESH_TOKEN_ID) != refresh_token_id:
            self._hass.config_entries.async_update_entry(
                entry,
                data={**entry.data, CONF_REFRESH_TOKEN_ID: refresh_token_id},
            )

        _LOGGER.info(
            "Bootstrap issued for user %s dashboard %s",
            result.user_id,
            result.dashboard_path,
        )
        return self.json(
            build_bootstrap_payload(
                result, hass_url=hass_url, hass_tokens=hass_tokens
            )
        )


def async_register_bootstrap_view(
    hass: HomeAssistant,
    token_service: AuthTokenService,
    rate_limiter: BootstrapRateLimiter | None = None,
) -> None:
    """Register the bootstrap HTTP view once."""
    hass.http.register_view(
        KPanelBootstrapView(hass, token_service, rate_limiter=rate_limiter)
    )
