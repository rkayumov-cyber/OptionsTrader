"""AggregatedProvider - wraps primary provider with MCP fallbacks."""

import logging

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
from mcp_server.providers.base import MarketDataProvider

from .manager import MCPClientManager
from .tool_mapping import ToolMapper

logger = logging.getLogger(__name__)


class AggregatedProvider(MarketDataProvider):
    """Provider that wraps a primary provider and falls back to MCP servers."""

    name = "aggregated"
    supported_markets: list[Market] = ["US", "JP", "HK"]

    def __init__(
        self,
        primary: MarketDataProvider,
        mcp_manager: MCPClientManager,
    ):
        self._primary = primary
        self._mcp = mcp_manager

    @property
    def primary(self) -> MarketDataProvider:
        return self._primary

    @primary.setter
    def primary(self, provider: MarketDataProvider) -> None:
        self._primary = provider

    # ── Core methods: try primary, fall back to MCP ──

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        try:
            return await self._primary.get_quote(symbol, market)
        except Exception as primary_err:
            logger.debug("Primary get_quote failed: %s, trying MCP fallback", primary_err)
            result = await self._mcp.call_tool_with_fallback(
                "quote", "get_quote", {"ticker": symbol}
            )
            if result and result.success:
                quote = ToolMapper.parse_quote(result.data, symbol, market)
                if quote:
                    return quote
            raise  # Re-raise original error if fallback fails

    async def get_option_chain(
        self, symbol: str, market: Market, expiration: str | None = None
    ) -> OptionChain:
        try:
            return await self._primary.get_option_chain(symbol, market, expiration)
        except Exception as primary_err:
            logger.debug("Primary get_option_chain failed: %s, trying MCP fallback", primary_err)
            # Yahoo MCP requires expiration_date and option_type
            if not expiration:
                # First get available expirations
                exp_result = await self._mcp.call_tool_with_fallback(
                    "options", "get_option_expirations", {"ticker": symbol}
                )
                if exp_result and exp_result.success and exp_result.data:
                    exps = exp_result.data if isinstance(exp_result.data, list) else []
                    expiration = exps[0] if exps else None
            if not expiration:
                raise
            # Fetch calls and puts separately and merge
            calls_result = await self._mcp.call_tool_with_fallback(
                "options", "get_option_chain",
                {"ticker": symbol, "expiration_date": expiration, "option_type": "calls"},
            )
            puts_result = await self._mcp.call_tool_with_fallback(
                "options", "get_option_chain",
                {"ticker": symbol, "expiration_date": expiration, "option_type": "puts"},
            )
            merged = {}
            if calls_result and calls_result.success:
                merged["calls"] = calls_result.data if isinstance(calls_result.data, list) else calls_result.data.get("calls", []) if isinstance(calls_result.data, dict) else []
            if puts_result and puts_result.success:
                merged["puts"] = puts_result.data if isinstance(puts_result.data, list) else puts_result.data.get("puts", []) if isinstance(puts_result.data, dict) else []
            if merged:
                chain = ToolMapper.parse_option_chain(merged, symbol, market)
                if chain:
                    return chain
            raise

    async def get_volatility_surface(
        self, symbol: str, market: Market
    ) -> VolatilitySurface:
        # No MCP fallback for vol surface (complex data structure)
        return await self._primary.get_volatility_surface(symbol, market)

    async def get_price_history(
        self, symbol: str, market: Market, interval: str = "1d", limit: int = 30
    ) -> PriceHistory:
        try:
            return await self._primary.get_price_history(symbol, market, interval, limit)
        except Exception as primary_err:
            logger.debug("Primary get_price_history failed: %s, trying MCP fallback", primary_err)
            # Map interval to Yahoo format
            period_map = {"1d": "1mo", "1h": "5d", "5m": "1d"}
            result = await self._mcp.call_tool_with_fallback(
                "history",
                "get_price_history",
                {
                    "ticker": symbol,
                    "period": period_map.get(interval, "1mo"),
                    "interval": interval,
                },
            )
            if result and result.success:
                history = ToolMapper.parse_price_history(
                    result.data, symbol, market, interval
                )
                if history:
                    return history
            raise

    # ── Optional methods: try primary, on NotImplementedError use MCP ──

    async def get_iv_analysis(self, symbol: str, market: Market) -> IVAnalysis:
        try:
            return await self._primary.get_iv_analysis(symbol, market)
        except Exception as e:
            logger.debug("Primary IV analysis failed (%s), trying MCP", type(e).__name__)
            # Get stock info for price/52-week data
            result = await self._mcp.call_tool_with_fallback(
                "quote", "get_quote", {"ticker": symbol}
            )
            if result and result.success:
                analysis = ToolMapper.build_iv_analysis(result.data, symbol, market)
                if analysis:
                    return analysis
            # Try deriving from option chain ATM IV
            exp_result = await self._mcp.call_tool_with_fallback(
                "options", "get_option_expirations", {"ticker": symbol}
            )
            if exp_result and exp_result.success and exp_result.data:
                exps = exp_result.data if isinstance(exp_result.data, list) else []
                if exps:
                    chain_result = await self._mcp.call_tool_with_fallback(
                        "options", "get_option_chain",
                        {"ticker": symbol, "expiration_date": exps[0], "option_type": "calls"},
                    )
                    if chain_result and chain_result.success:
                        analysis = ToolMapper.build_iv_from_chain(
                            chain_result.data, result.data if result else {}, symbol, market
                        )
                        if analysis:
                            return analysis
            raise NotImplementedError("IV analysis not available from any source")

    async def get_market_sentiment(
        self, symbol: str, market: Market
    ) -> MarketSentiment:
        try:
            return await self._primary.get_market_sentiment(symbol, market)
        except Exception as e:
            logger.debug("Primary sentiment failed (%s), trying MCP", type(e).__name__)
            result = await self._mcp.call_tool_with_fallback(
                "sentiment", "get_sentiment",
                {"ticker": symbol, "recommendation_type": "upgrades_downgrades"},
            )
            if result and result.success:
                sentiment = ToolMapper.parse_market_sentiment(
                    result.data, symbol, market
                )
                if sentiment:
                    return sentiment
            raise NotImplementedError("Market sentiment not available from any source")

    async def get_unusual_activity(
        self, market: Market | None = None
    ) -> UnusualActivityResponse:
        # No MCP fallback for unusual activity
        return await self._primary.get_unusual_activity(market)

    async def get_strategy_suggestions(
        self, symbol: str, market: Market
    ) -> StrategySuggestionsResponse:
        # No MCP fallback for strategy suggestions
        return await self._primary.get_strategy_suggestions(symbol, market)
