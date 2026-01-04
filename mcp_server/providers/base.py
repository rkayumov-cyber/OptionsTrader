"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod

from mcp_server.models import (
    Market,
    OptionChain,
    Quote,
    VolatilitySurface,
)


class MarketDataProvider(ABC):
    """Abstract interface for market data providers."""

    name: str
    supported_markets: list[Market]

    @abstractmethod
    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Get real-time quote for a symbol.

        Args:
            symbol: Ticker symbol (e.g., "AAPL", "7203.T", "0700.HK")
            market: Market identifier

        Returns:
            Quote with current price data
        """
        ...

    @abstractmethod
    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Get option chain for a symbol.

        Args:
            symbol: Underlying ticker symbol
            market: Market identifier
            expiration: Optional specific expiration date (YYYY-MM-DD)

        Returns:
            OptionChain with calls and puts
        """
        ...

    @abstractmethod
    async def get_volatility_surface(
        self,
        symbol: str,
        market: Market,
    ) -> VolatilitySurface:
        """Get implied volatility surface.

        Args:
            symbol: Underlying ticker symbol
            market: Market identifier

        Returns:
            VolatilitySurface with IV grid across strikes and expirations
        """
        ...

    def supports_market(self, market: Market) -> bool:
        """Check if provider supports a market."""
        return market in self.supported_markets
