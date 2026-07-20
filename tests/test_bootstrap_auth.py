"""Tests for bootstrap binding-secret auth helper."""

import pytest

from custom_components.kpanel_dashboard.bootstrap_auth import (
    BINDING_SECRET_HEADER,
    BootstrapAuthError,
    validate_binding_secret,
)


def test_header_constant() -> None:
    assert BINDING_SECRET_HEADER == "X-KPanel-Binding-Secret"


def test_validate_accepts_matching_secret() -> None:
    validate_binding_secret(provided="abc", expected="abc")


def test_validate_rejects_missing_provided() -> None:
    with pytest.raises(BootstrapAuthError, match="missing"):
        validate_binding_secret(provided=None, expected="abc")


def test_validate_rejects_mismatch() -> None:
    with pytest.raises(BootstrapAuthError, match="invalid"):
        validate_binding_secret(provided="wrong", expected="abc")


def test_validate_rejects_when_expected_missing() -> None:
    with pytest.raises(BootstrapAuthError, match="not configured"):
        validate_binding_secret(provided="abc", expected=None)
