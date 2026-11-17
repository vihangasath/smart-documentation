"""Small in-memory sliding-window rate limiter (per process)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    """Allow at most ``limit`` hits per ``window_seconds`` for each key."""

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> float | None:
        """
        Record a hit for ``key``.

        Returns ``None`` when allowed, or the number of seconds to wait
        before the next hit would be allowed.
        """
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return max(self._window - (now - hits[0]), 1.0)
        hits.append(now)
        if len(self._hits) > 10_000:  # opportunistic cleanup of idle keys
            for k in [
                k for k, v in self._hits.items() if not v or now - v[-1] >= self._window
            ]:
                del self._hits[k]
        return None
