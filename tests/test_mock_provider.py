"""Tests for the mock data provider."""

from datetime import date, datetime

import pytest

from mcp_server.models import (
    Greeks,
    Market,
    OptionChain,
    OptionContract,
    Quote,
    VolatilitySurface,
)
from mcp_server.providers.mock import MockProvider, MOCK_STOCKS


@pytest.fixture
def provider() -> MockProvider:
    """Create a mock provider instance."""
    return MockProvider()


class TestMockProviderConfig:
    """Test provider configuration."""

    def test_name(self, provider: MockProvider):
        assert provider.name == "mock"

    def test_supported_markets(self, provider: MockProvider):
        assert provider.supported_markets == ["US", "JP", "HK"]

    @pytest.mark.parametrize("market", ["US", "JP", "HK"])
    def test_supports_market(self, provider: MockProvider, market: Market):
        assert provider.supports_market(market) is True


class TestGetQuote:
    """Test get_quote method."""

    @pytest.mark.asyncio
    async def test_returns_quote_object(self, provider: MockProvider):
        quote = await provider.get_quote("AAPL", "US")
        assert isinstance(quote, Quote)

    @pytest.mark.asyncio
    async def test_quote_has_required_fields(self, provider: MockProvider):
        quote = await provider.get_quote("AAPL", "US")
        assert quote.symbol == "AAPL"
        assert quote.market == "US"
        assert quote.price > 0
        assert quote.volume > 0
        assert isinstance(quote.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_quote_has_bid_ask(self, provider: MockProvider):
        quote = await provider.get_quote("AAPL", "US")
        assert quote.bid is not None
        assert quote.ask is not None
        assert quote.bid < quote.ask

    @pytest.mark.asyncio
    async def test_known_stock_uses_base_price(self, provider: MockProvider):
        quote = await provider.get_quote("AAPL", "US")
        base_price = MOCK_STOCKS["US"]["AAPL"]["price"]
        # Price should be within 0.1% of base price
        assert abs(quote.price - base_price) / base_price < 0.01

    @pytest.mark.asyncio
    async def test_unknown_stock_uses_default_price(self, provider: MockProvider):
        quote = await provider.get_quote("UNKNOWN", "US")
        # Default base price is 100.0
        assert 99 < quote.price < 101

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "symbol,market",
        [
            ("AAPL", "US"),
            ("7203.T", "JP"),
            ("0700.HK", "HK"),
        ],
    )
    async def test_different_markets(
        self, provider: MockProvider, symbol: str, market: Market
    ):
        quote = await provider.get_quote(symbol, market)
        assert quote.symbol == symbol
        assert quote.market == market


class TestGetOptionChain:
    """Test get_option_chain method."""

    @pytest.mark.asyncio
    async def test_returns_option_chain(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        assert isinstance(chain, OptionChain)

    @pytest.mark.asyncio
    async def test_chain_has_required_fields(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        assert chain.underlying == "AAPL"
        assert chain.market == "US"
        assert len(chain.expirations) > 0
        assert len(chain.calls) > 0
        assert len(chain.puts) > 0
        assert isinstance(chain.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_chain_has_multiple_expirations(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        assert len(chain.expirations) >= 4

    @pytest.mark.asyncio
    async def test_calls_are_call_type(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        for call in chain.calls:
            assert call.option_type == "call"

    @pytest.mark.asyncio
    async def test_puts_are_put_type(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        for put in chain.puts:
            assert put.option_type == "put"

    @pytest.mark.asyncio
    async def test_options_have_greeks(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        for call in chain.calls:
            assert call.greeks is not None
            assert isinstance(call.greeks, Greeks)

    @pytest.mark.asyncio
    async def test_options_have_implied_volatility(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        for call in chain.calls:
            assert call.implied_volatility is not None
            assert call.implied_volatility > 0

    @pytest.mark.asyncio
    async def test_filter_by_expiration(self, provider: MockProvider):
        chain_all = await provider.get_option_chain("AAPL", "US")
        first_exp = chain_all.expirations[0]

        chain_filtered = await provider.get_option_chain(
            "AAPL", "US", expiration=str(first_exp)
        )
        assert len(chain_filtered.expirations) == 1
        assert chain_filtered.expirations[0] == first_exp

    @pytest.mark.asyncio
    async def test_strikes_around_underlying_price(self, provider: MockProvider):
        chain = await provider.get_option_chain("AAPL", "US")
        quote = await provider.get_quote("AAPL", "US")

        strikes = sorted(set(c.strike for c in chain.calls))
        # Should have strikes both above and below current price
        assert any(s < quote.price for s in strikes)
        assert any(s > quote.price for s in strikes)


class TestGetVolatilitySurface:
    """Test get_volatility_surface method."""

    @pytest.mark.asyncio
    async def test_returns_volatility_surface(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        assert isinstance(surface, VolatilitySurface)

    @pytest.mark.asyncio
    async def test_surface_has_required_fields(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        assert surface.symbol == "AAPL"
        assert surface.market == "US"
        assert len(surface.strikes) > 0
        assert len(surface.expirations) > 0
        assert len(surface.call_ivs) > 0
        assert len(surface.put_ivs) > 0
        assert isinstance(surface.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_iv_grid_dimensions(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        num_expirations = len(surface.expirations)
        num_strikes = len(surface.strikes)

        # call_ivs should be [num_expirations][num_strikes]
        assert len(surface.call_ivs) == num_expirations
        for row in surface.call_ivs:
            assert len(row) == num_strikes

        assert len(surface.put_ivs) == num_expirations
        for row in surface.put_ivs:
            assert len(row) == num_strikes

    @pytest.mark.asyncio
    async def test_iv_values_are_reasonable(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        for row in surface.call_ivs:
            for iv in row:
                # IV should be between 0 and 2 (0% to 200%)
                assert 0 < iv < 2

    @pytest.mark.asyncio
    async def test_strikes_ordered(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        assert surface.strikes == sorted(surface.strikes)

    @pytest.mark.asyncio
    async def test_expirations_ordered(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        assert surface.expirations == sorted(surface.expirations)

    @pytest.mark.asyncio
    async def test_expirations_are_future_dates(self, provider: MockProvider):
        surface = await provider.get_volatility_surface("AAPL", "US")
        today = date.today()
        for exp in surface.expirations:
            assert exp > today
