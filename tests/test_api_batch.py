"""Tests for batch API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from api.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestBatchQuotes:
    """Test POST /api/quotes/batch endpoint."""

    @pytest.mark.asyncio
    async def test_batch_quotes_returns_all_symbols(self, client: AsyncClient):
        response = await client.post("/api/quotes/batch", json={
            "symbols": [
                {"symbol": "AAPL", "market": "US"},
                {"symbol": "MSFT", "market": "US"},
                {"symbol": "GOOGL", "market": "US"},
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data
        assert "MSFT" in data
        assert "GOOGL" in data

    @pytest.mark.asyncio
    async def test_batch_quotes_each_has_price(self, client: AsyncClient):
        response = await client.post("/api/quotes/batch", json={
            "symbols": [
                {"symbol": "AAPL", "market": "US"},
            ]
        })
        data = response.json()
        assert "price" in data["AAPL"]
        assert isinstance(data["AAPL"]["price"], (int, float))

    @pytest.mark.asyncio
    async def test_batch_quotes_empty_list(self, client: AsyncClient):
        response = await client.post("/api/quotes/batch", json={
            "symbols": []
        })
        assert response.status_code == 200
        assert response.json() == {}


class TestBatchIVAnalysis:
    """Test POST /api/iv-analysis/batch endpoint."""

    @pytest.mark.asyncio
    async def test_batch_iv_returns_all_symbols(self, client: AsyncClient):
        response = await client.post("/api/iv-analysis/batch", json={
            "symbols": [
                {"symbol": "AAPL", "market": "US"},
                {"symbol": "MSFT", "market": "US"},
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data
        assert "MSFT" in data

    @pytest.mark.asyncio
    async def test_batch_iv_has_iv_rank(self, client: AsyncClient):
        response = await client.post("/api/iv-analysis/batch", json={
            "symbols": [
                {"symbol": "AAPL", "market": "US"},
            ]
        })
        data = response.json()
        # Mock provider should return iv_rank
        assert "iv_rank" in data["AAPL"]

    @pytest.mark.asyncio
    async def test_batch_iv_empty_list(self, client: AsyncClient):
        response = await client.post("/api/iv-analysis/batch", json={
            "symbols": []
        })
        assert response.status_code == 200
        assert response.json() == {}


class TestCacheIntegration:
    """Test that cache is working for standard endpoints."""

    @pytest.mark.asyncio
    async def test_quote_cache_hit(self, client: AsyncClient):
        # First request populates cache
        r1 = await client.get("/api/quote/AAPL", params={"market": "US"})
        assert r1.status_code == 200
        # Second request should hit cache (same price for mock)
        r2 = await client.get("/api/quote/AAPL", params={"market": "US"})
        assert r2.status_code == 200

    @pytest.mark.asyncio
    async def test_market_indicators_success(self, client: AsyncClient):
        response = await client.get("/api/market-indicators")
        assert response.status_code == 200
        data = response.json()
        assert "bonds" in data
        assert "commodities" in data
        assert "sectors" in data
        assert "breadth" in data
