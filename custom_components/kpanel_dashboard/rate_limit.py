"""Simple sliding-window rate limiter for bootstrap requests."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable


class BootstrapRateLimiter:
    """Limit calls per key within a rolling time window."""

    def __init__(
        self,
        *,
        max_calls: int,
        window_seconds: float,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._time = time_fn or time.monotonic
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = self._time()
        bucket = self._hits[key]
        cutoff = now - self._window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._max_calls:
            return False
        bucket.append(now)
        return True
