"""Tests for bootstrap rate limiting."""

from custom_components.kpanel_dashboard.rate_limit import BootstrapRateLimiter


def test_allows_under_limit() -> None:
    limiter = BootstrapRateLimiter(max_calls=2, window_seconds=60.0, time_fn=lambda: 100.0)
    assert limiter.allow("secret-a") is True
    assert limiter.allow("secret-a") is True


def test_blocks_over_limit() -> None:
    now = {"t": 100.0}
    limiter = BootstrapRateLimiter(
        max_calls=2, window_seconds=60.0, time_fn=lambda: now["t"]
    )
    assert limiter.allow("secret-a") is True
    assert limiter.allow("secret-a") is True
    assert limiter.allow("secret-a") is False


def test_window_expiry_resets() -> None:
    now = {"t": 100.0}
    limiter = BootstrapRateLimiter(
        max_calls=1, window_seconds=10.0, time_fn=lambda: now["t"]
    )
    assert limiter.allow("secret-a") is True
    assert limiter.allow("secret-a") is False
    now["t"] = 111.0
    assert limiter.allow("secret-a") is True


def test_keys_are_independent() -> None:
    limiter = BootstrapRateLimiter(max_calls=1, window_seconds=60.0, time_fn=lambda: 1.0)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False
