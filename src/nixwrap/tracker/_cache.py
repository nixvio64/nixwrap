"""Thread-safe TTL cache for player stats.

Tracker.gg updates every about 5 minutes, so we cache aggressively and
never poll continuously.  Fetches are event-driven (new player appears
in match -> fetch once).
"""

from __future__ import annotations

import threading
import time
from typing import Any


DEFAULT_TTL = 300  # seconds


class TTLCache:
    """A thread-safe dictionary with time-to-live expiry.

    Parameters
    ttl:
        Default time-to-live in seconds.  Entries older than this are
        considered stale.
    """

    def __init__(self, ttl: float = DEFAULT_TTL) -> None:
        self._ttl = ttl
        self._data: dict[str, tuple[float, float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Return the cached value if it exists and is not expired,
        otherwise None.
        """
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            timestamp, entry_ttl, value = entry
            if time.time() - timestamp > entry_ttl:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store value in the cache with the current timestamp.

        Parameters
        ----------
        ttl:
            Per-entry TTL override.  Uses the cache-wide default when
            ``None``.
        """
        with self._lock:
            self._data[key] = (time.time(), ttl if ttl is not None else self._ttl, value)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from the cache."""
        with self._lock:
            self._data.pop(key, None)

    def clear(self) -> None:
        """Remove all entries."""
        with self._lock:
            self._data.clear()

    def invalidate_old(self) -> int:
        """Remove all expired entries.  Returns the count removed."""
        now = time.time()
        removed = 0
        with self._lock:
            stale = [
                k for k, (ts, entry_ttl, _) in self._data.items()
                if now - ts > entry_ttl
            ]
            for k in stale:
                del self._data[k]
                removed += 1
        return removed

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None
