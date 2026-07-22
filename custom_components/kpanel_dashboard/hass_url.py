"""Resolve the Home Assistant base URL used in hassTokens / bootstrap."""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse

from homeassistant.core import HomeAssistant

from .const import CONF_LOCAL_HASS_URL


def normalize_hass_base_url(url: str) -> str:
    cleaned = (url or "").strip().rstrip("/")
    if not cleaned:
        raise ValueError("local_hass_url is required when provided")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("local_hass_url must be an absolute http(s) URL")
    return cleaned


def resolve_hass_base_url(
    hass: HomeAssistant,
    *,
    entry_data: Mapping[str, Any] | None = None,
    request_origin: str | None = None,
) -> str:
    """
    Base URL embedded in hassTokens and dashboard_url.

    Prefer an explicit local override (LAN IP for kiosks), then HA internal URL,
    then external URL, then the HTTP request origin.
    """
    if entry_data:
        configured = entry_data.get(CONF_LOCAL_HASS_URL)
        if isinstance(configured, str) and configured.strip():
            return normalize_hass_base_url(configured)

    internal = getattr(hass.config, "internal_url", None)
    if internal:
        return str(internal).rstrip("/")

    external = getattr(hass.config, "external_url", None)
    if external:
        return str(external).rstrip("/")

    if request_origin:
        return str(request_origin).rstrip("/")

    return "http://homeassistant.local:8123"
