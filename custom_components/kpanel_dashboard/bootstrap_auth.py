"""Bootstrap binding-secret authentication."""

from __future__ import annotations

import hmac

from .const import BINDING_SECRET_HEADER

__all__ = [
    "BINDING_SECRET_HEADER",
    "BootstrapAuthError",
    "validate_binding_secret",
]


class BootstrapAuthError(Exception):
    """Raised when bootstrap binding authentication fails."""


def validate_binding_secret(*, provided: str | None, expected: str | None) -> None:
    """Validate the shared binding secret using constant-time compare."""
    if not expected:
        raise BootstrapAuthError("binding secret not configured")
    if not provided:
        raise BootstrapAuthError("binding secret missing")
    if not hmac.compare_digest(provided, expected):
        raise BootstrapAuthError("binding secret invalid")
