"""Async-safe in-memory TTL cache with request deduplication."""

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# Default TTL values by category (seconds)
TTL_QUOTES = 10
TTL_IV_ANALYSIS = 30
TTL_SENTIMENT = 60
TTL_MARKET_INDICATORS = 15
TTL_FEAR_GREED = 120
TTL_OPTIONS = 30


class TTLCache:
    """In-memory TTL cache with per-key async deduplication.

    When multiple concurrent requests ask for the same key, only one
    actually calls the provider — the rest await the same result.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], Awaitable[Any]],
        ttl_seconds: float,
    ) -> Any:
        """Return cached value or call fetch_fn, caching the result.

        Concurrent callers for the same key are coalesced — only one
        invocation of fetch_fn runs; the rest await its result.
        """
        # Fast path: check cache without lock
        entry = self._store.get(key)
        if entry is not None:
            value, expire_at = entry
            if time.monotonic() < expire_at:
                return value

        # Slow path: acquire per-key lock, double-check, then fetch
        lock = self._get_lock(key)
        async with lock:
            # Double-check after acquiring lock
            entry = self._store.get(key)
            if entry is not None:
                value, expire_at = entry
                if time.monotonic() < expire_at:
                    return value

            # Actually fetch
            value = await fetch_fn()
            self._store[key] = (value, time.monotonic() + ttl_seconds)
            return value

    def get(self, key: str) -> Any | None:
        """Get a cached value without fetching. Returns None if missing/expired."""
        entry = self._store.get(key)
        if entry is not None:
            value, expire_at = entry
            if time.monotonic() < expire_at:
                return value
            # Expired — clean up
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Manually set a cache entry."""
        self._store[key] = (value, time.monotonic() + ttl_seconds)

    def invalidate(self, key: str) -> bool:
        """Remove a single key. Returns True if it existed."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Remove all keys starting with prefix. Returns count removed."""
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]
        return len(keys)

    def clear(self) -> None:
        """Remove all cached entries."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Number of entries (including potentially expired ones)."""
        return len(self._store)

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        now = time.monotonic()
        active = sum(1 for _, (_, exp) in self._store.items() if exp > now)
        return {
            "total_entries": len(self._store),
            "active_entries": active,
            "expired_entries": len(self._store) - active,
        }
