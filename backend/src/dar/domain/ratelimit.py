from __future__ import annotations

import math
from collections import defaultdict, deque
from collections.abc import Callable


class SlidingWindowLimiter:
    """Allow at most `limit` hits per key within `window` seconds. The clock is injected for testing."""

    def __init__(self, limit: int, clock: Callable[[], float], window: float = 60.0) -> None:
        self._limit = limit
        self._window = window
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds). Records the hit only when allowed."""
        now = self._clock()
        hits = self._hits[key]
        while hits and now - hits[0] >= self._window:
            hits.popleft()
        if len(hits) >= self._limit:
            return False, max(1, math.ceil(self._window - (now - hits[0])))
        hits.append(now)
        return True, 0
