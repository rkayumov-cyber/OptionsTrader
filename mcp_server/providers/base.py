"""Abstract base class for market data providers."""

from abc import ABC, abstractmethod

from mcp_server.models import (
    IVAnalysis,
    Market,
    MarketSentiment,
    OptionChain,
    PriceHistory,
    Quote,
    StrategySuggestionsResponse,
    UnusualActivityResponse,
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

    @abstractmethod
    async def get_price_history(
        self,
        symbol: str,
        market: Market,
        interval: str = "1d",
        limit: int = 30,
    ) -> PriceHistory:
        """Get historical price data.

        Args:
            symbol: Ticker symbol
            market: Market identifier
            interval: Time interval ("1d", "1h", "5m")
            limit: Number of bars to return

        Returns:
            PriceHistory with OHLCV bars
        """
        ...

    # Dashboard methods - optional, with default implementations

    async def get_iv_analysis(
        self,
        symbol: str,
        market: Market,
    ) -> IVAnalysis:
        """Get IV rank and percentile analysis.

        Args:
            symbol: Ticker symbol
            market: Market identifier

        Returns:
            IVAnalysis with IV rank, percentile, and historical range
        """
        raise NotImplementedError("IV analysis not supported by this provider")

    async def get_market_sentiment(
        self,
        symbol: str,
        market: Market,
    ) -> MarketSentiment:
        """Get put/call ratio and sentiment indicators.

        Args:
            symbol: Ticker symbol
            market: Market identifier

        Returns:
            MarketSentiment with P/C ratio and sentiment classification
        """
        raise NotImplementedError("Market sentiment not supported by this provider")

    async def get_unusual_activity(
        self,
        market: Market | None = None,
    ) -> UnusualActivityResponse:
        """Get unusual options activity alerts.

        Args:
            market: Optional market filter

        Returns:
            UnusualActivityResponse with list of alerts
        """
        raise NotImplementedError("Unusual activity not supported by this provider")

    async def get_strategy_suggestions(
        self,
        symbol: str,
        market: Market,
    ) -> StrategySuggestionsResponse:
        """Get strategy recommendations based on market conditions.

        Args:
            symbol: Ticker symbol
            market: Market identifier

        Returns:
            StrategySuggestionsResponse with suggested strategies
        """
        raise NotImplementedError("Strategy suggestions not supported by this provider")

    def supports_market(self, market: Market) -> bool:
        """Check if provider supports a market."""
        return market in self.supported_markets
