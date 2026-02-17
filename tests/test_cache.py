"""Tests for the TTL cache module."""

import asyncio
import time

import pytest

from api.cache import TTLCache


@pytest.fixture
def cache() -> TTLCache:
    return TTLCache()


class TestTTLCache:
    """Core cache behavior."""

    @pytest.mark.asyncio
    async def test_get_or_fetch_stores_value(self, cache: TTLCache):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return {"price": 100}

        result = await cache.get_or_fetch("quote:AAPL", fetch, ttl_seconds=10)
        assert result == {"price": 100}
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_get_or_fetch_returns_cached(self, cache: TTLCache):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return {"price": 100}

        await cache.get_or_fetch("quote:AAPL", fetch, ttl_seconds=10)
        result2 = await cache.get_or_fetch("quote:AAPL", fetch, ttl_seconds=10)
        assert result2 == {"price": 100}
        assert call_count == 1  # Only fetched once

    @pytest.mark.asyncio
    async def test_ttl_expiry(self, cache: TTLCache):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return call_count

        await cache.get_or_fetch("key", fetch, ttl_seconds=0.05)
        assert call_count == 1

        await asyncio.sleep(0.1)  # Wait for expiry

        result = await cache.get_or_fetch("key", fetch, ttl_seconds=0.05)
        assert call_count == 2
        assert result == 2

    @pytest.mark.asyncio
    async def test_concurrent_deduplication(self, cache: TTLCache):
        """Multiple concurrent requests for the same key should only call fetch once."""
        call_count = 0

        async def slow_fetch():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return {"price": 42}

        results = await asyncio.gather(
            cache.get_or_fetch("quote:AAPL", slow_fetch, ttl_seconds=10),
            cache.get_or_fetch("quote:AAPL", slow_fetch, ttl_seconds=10),
            cache.get_or_fetch("quote:AAPL", slow_fetch, ttl_seconds=10),
            cache.get_or_fetch("quote:AAPL", slow_fetch, ttl_seconds=10),
            cache.get_or_fetch("quote:AAPL", slow_fetch, ttl_seconds=10),
        )

        assert all(r == {"price": 42} for r in results)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_different_keys_not_deduplicated(self, cache: TTLCache):
        call_count = 0

        async def fetch():
            nonlocal call_count
            call_count += 1
            return call_count

        r1 = await cache.get_or_fetch("a", fetch, ttl_seconds=10)
        r2 = await cache.get_or_fetch("b", fetch, ttl_seconds=10)
        assert r1 == 1
        assert r2 == 2
        assert call_count == 2

    def test_invalidate(self, cache: TTLCache):
        cache.set("k1", "v1", 60)
        assert cache.get("k1") == "v1"

        assert cache.invalidate("k1") is True
        assert cache.get("k1") is None

        assert cache.invalidate("k1") is False  # Already gone

    def test_invalidate_prefix(self, cache: TTLCache):
        cache.set("quote:AAPL:US", 1, 60)
        cache.set("quote:MSFT:US", 2, 60)
        cache.set("iv:AAPL:US", 3, 60)

        removed = cache.invalidate_prefix("quote:")
        assert removed == 2
        assert cache.get("quote:AAPL:US") is None
        assert cache.get("iv:AAPL:US") == 3

    def test_clear(self, cache: TTLCache):
        cache.set("a", 1, 60)
        cache.set("b", 2, 60)
        assert cache.size == 2

        cache.clear()
        assert cache.size == 0

    def test_get_expired(self, cache: TTLCache):
        cache.set("k", "v", 0)  # Expires immediately
        # Manually set past expiry
        cache._store["k"] = ("v", time.monotonic() - 1)
        assert cache.get("k") is None

    def test_set_and_get(self, cache: TTLCache):
        cache.set("k", {"data": True}, 60)
        assert cache.get("k") == {"data": True}

    def test_stats(self, cache: TTLCache):
        cache.set("active", "v", 60)
        cache._store["expired"] = ("v", time.monotonic() - 1)

        stats = cache.stats()
        assert stats["total_entries"] == 2
        assert stats["active_entries"] == 1
        assert stats["expired_entries"] == 1

    @pytest.mark.asyncio
    async def test_fetch_exception_not_cached(self, cache: TTLCache):
        """If fetch raises, the error should propagate and nothing is cached."""

        async def bad_fetch():
            raise ValueError("provider down")

        with pytest.raises(ValueError, match="provider down"):
            await cache.get_or_fetch("key", bad_fetch, ttl_seconds=10)

        assert cache.get("key") is None
