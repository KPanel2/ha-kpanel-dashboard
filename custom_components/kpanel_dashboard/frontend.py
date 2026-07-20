"""Register kiosk chrome JS with the HA frontend."""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, add_extra_js_url
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_when_setup

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

KIOSK_JS_URL = f"/{DOMAIN}/kpanel-kiosk.js"
KIOSK_JS_FILE = Path(__file__).parent / "www" / "kpanel-kiosk.js"


async def _async_register_static_path(hass: HomeAssistant) -> None:
    try:
        from homeassistant.components.http import StaticPathConfig
    except ImportError:  # Home Assistant < 2024.6
        StaticPathConfig = None  # type: ignore[misc, assignment]

    if StaticPathConfig is not None and hasattr(
        hass.http, "async_register_static_paths"
    ):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(KIOSK_JS_URL, str(KIOSK_JS_FILE), True)]
        )
        return

    hass.http.register_static_path(KIOSK_JS_URL, str(KIOSK_JS_FILE), True)


async def _async_add_extra_js(hass: HomeAssistant, _component: str) -> None:
    add_extra_js_url(hass, KIOSK_JS_URL)
    _LOGGER.debug("Added KPanel kiosk module URL %s", KIOSK_JS_URL)


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the kiosk chrome module and load it once frontend is ready."""
    if hass.data.get(DOMAIN, {}).get("_frontend_registered"):
        return

    if not KIOSK_JS_FILE.is_file():
        _LOGGER.error("Missing kiosk frontend bundle at %s", KIOSK_JS_FILE)
        return

    await _async_register_static_path(hass)

    # Frontend may not be loaded yet in tests / early setup; wait for it.
    if DATA_EXTRA_MODULE_URL in hass.data:
        await _async_add_extra_js(hass, "frontend")
    else:
        async_when_setup(hass, "frontend", _async_add_extra_js)

    hass.data.setdefault(DOMAIN, {})["_frontend_registered"] = True
    _LOGGER.debug("Registered KPanel kiosk static path at %s", KIOSK_JS_URL)
