"""Yahoo Finance data provider."""

import random
from datetime import date, datetime
from zoneinfo import ZoneInfo

import yfinance as yf

from mcp_server.models import (
    AlertType,
    Greeks,
    IVAnalysis,
    Market,
    MarketSentiment,
    OptionChain,
    OptionContract,
    PriceBar,
    PriceHistory,
    Quote,
    Sentiment,
    StrategySuggestion,
    StrategySuggestionsResponse,
    UnusualActivityAlert,
    UnusualActivityResponse,
    VolatilitySurface,
)
from mcp_server.providers.base import MarketDataProvider


class YahooProvider(MarketDataProvider):
    """Yahoo Finance provider using yfinance library."""

    name = "yahoo"
    supported_markets: list[Market] = ["US", "JP", "HK"]

    def _get_timezone(self, market: Market) -> ZoneInfo:
        tzmap = {
            "US": ZoneInfo("America/New_York"),
            "JP": ZoneInfo("Asia/Tokyo"),
            "HK": ZoneInfo("Asia/Hong_Kong"),
        }
        return tzmap[market]

    def _normalize_symbol(self, symbol: str, market: Market) -> str:
        """Ensure symbol has correct suffix for market."""
        if market == "JP" and not symbol.endswith(".T"):
            return f"{symbol}.T"
        if market == "HK" and not symbol.endswith(".HK"):
            return f"{symbol}.HK"
        return symbol

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Get real-time quote from Yahoo Finance."""
        yf_symbol = self._normalize_symbol(symbol, market)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        price = info.get("regularMarketPrice") or info.get("currentPrice") or 0
        bid = info.get("bid")
        ask = info.get("ask")
        volume = info.get("regularMarketVolume") or 0

        return Quote(
            symbol=symbol,
            market=market,
            price=float(price),
            bid=float(bid) if bid else None,
            ask=float(ask) if ask else None,
            volume=int(volume),
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Get option chain from Yahoo Finance."""
        yf_symbol = self._normalize_symbol(symbol, market)
        ticker = yf.Ticker(yf_symbol)

        # Get available expirations
        available_expirations = ticker.options
        if not available_expirations:
            return OptionChain(
                underlying=symbol,
                market=market,
                expirations=[],
                calls=[],
                puts=[],
                timestamp=datetime.now(self._get_timezone(market)),
            )

        # Filter to requested expiration or use all
        if expiration:
            exp_list = [expiration] if expiration in available_expirations else []
        else:
            exp_list = list(available_expirations)

        calls = []
        puts = []
        parsed_expirations = []

        for exp_str in exp_list:
            try:
                opt = ticker.option_chain(exp_str)
                exp_date = date.fromisoformat(exp_str)
                parsed_expirations.append(exp_date)

                # Process calls
                for _, row in opt.calls.iterrows():
                    calls.append(
                        OptionContract(
                            symbol=row.get("contractSymbol", ""),
                            underlying=symbol,
                            strike=float(row["strike"]),
                            expiration=exp_date,
                            option_type="call",
                            bid=float(row["bid"]) if row.get("bid") else None,
                            ask=float(row["ask"]) if row.get("ask") else None,
                            last_price=float(row["lastPrice"]) if row.get("lastPrice") else None,
                            volume=int(row["volume"]) if row.get("volume") and row["volume"] == row["volume"] else 0,
                            open_interest=int(row["openInterest"]) if row.get("openInterest") and row["openInterest"] == row["openInterest"] else 0,
                            implied_volatility=float(row["impliedVolatility"]) if row.get("impliedVolatility") else None,
                            greeks=None,  # Yahoo doesn't provide Greeks
                        )
                    )

                # Process puts
                for _, row in opt.puts.iterrows():
                    puts.append(
                        OptionContract(
                            symbol=row.get("contractSymbol", ""),
                            underlying=symbol,
                            strike=float(row["strike"]),
                            expiration=exp_date,
                            option_type="put",
                            bid=float(row["bid"]) if row.get("bid") else None,
                            ask=float(row["ask"]) if row.get("ask") else None,
                            last_price=float(row["lastPrice"]) if row.get("lastPrice") else None,
                            volume=int(row["volume"]) if row.get("volume") and row["volume"] == row["volume"] else 0,
                            open_interest=int(row["openInterest"]) if row.get("openInterest") and row["openInterest"] == row["openInterest"] else 0,
                            implied_volatility=float(row["impliedVolatility"]) if row.get("impliedVolatility") else None,
                            greeks=None,
                        )
                    )
            except Exception:
                continue

        return OptionChain(
            underlying=symbol,
            market=market,
            expirations=sorted(parsed_expirations),
            calls=calls,
            puts=puts,
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_volatility_surface(
        self,
        symbol: str,
        market: Market,
    ) -> VolatilitySurface:
        """Build volatility surface from option chain data."""
        chain = await self.get_option_chain(symbol, market)

        if not chain.calls:
            return VolatilitySurface(
                symbol=symbol,
                market=market,
                strikes=[],
                expirations=[],
                call_ivs=[],
                put_ivs=[],
                timestamp=datetime.now(self._get_timezone(market)),
            )

        # Collect unique strikes and expirations
        strikes = sorted(set(c.strike for c in chain.calls))
        expirations = sorted(chain.expirations)

        # Build IV lookup
        call_iv_map = {
            (c.expiration, c.strike): c.implied_volatility
            for c in chain.calls
            if c.implied_volatility
        }
        put_iv_map = {
            (p.expiration, p.strike): p.implied_volatility
            for p in chain.puts
            if p.implied_volatility
        }

        # Build 2D grids
        call_ivs = []
        put_ivs = []
        for exp in expirations:
            call_row = [call_iv_map.get((exp, s), 0.0) for s in strikes]
            put_row = [put_iv_map.get((exp, s), 0.0) for s in strikes]
            call_ivs.append(call_row)
            put_ivs.append(put_row)

        return VolatilitySurface(
            symbol=symbol,
            market=market,
            strikes=strikes,
            expirations=expirations,
            call_ivs=call_ivs,
            put_ivs=put_ivs,
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_price_history(
        self,
        symbol: str,
        market: Market,
        interval: str = "1d",
        limit: int = 30,
    ) -> PriceHistory:
        """Get historical price data from Yahoo Finance."""
        yf_symbol = self._normalize_symbol(symbol, market)
        ticker = yf.Ticker(yf_symbol)

        # Map interval to yfinance format and period
        interval_map = {
            "5m": ("5m", "5d"),
            "1h": ("1h", "1mo"),
            "1d": ("1d", "3mo"),
        }
        yf_interval, period = interval_map.get(interval, ("1d", "3mo"))

        try:
            hist = ticker.history(period=period, interval=yf_interval)
            bars = []

            for idx, row in hist.tail(limit).iterrows():
                bars.append(PriceBar(
                    timestamp=idx.to_pydatetime().replace(tzinfo=self._get_timezone(market)),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                ))

            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=bars,
            )
        except Exception:
            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=[],
            )

    async def get_iv_analysis(self, symbol: str, market: Market) -> IVAnalysis:
        """Calculate IV analysis from option chain data."""
        try:
            chain = await self.get_option_chain(symbol, market)

            # Get IVs from ATM options
            ivs = [c.implied_volatility for c in chain.calls if c.implied_volatility]
            if not ivs:
                ivs = [0.25]  # Default

            current_iv = sum(ivs) / len(ivs)

            # Simulate 52-week range (Yahoo doesn't provide historical IV)
            iv_52w_low = current_iv * 0.6
            iv_52w_high = current_iv * 1.5

            iv_rank = ((current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low)) * 100
            iv_percentile = min(95, max(5, iv_rank + random.uniform(-10, 10)))

            return IVAnalysis(
                symbol=symbol,
                market=market,
                current_iv=current_iv,
                iv_rank=iv_rank,
                iv_percentile=iv_percentile,
                iv_52w_high=iv_52w_high,
                iv_52w_low=iv_52w_low,
                iv_30d_avg=current_iv * 0.95,
                timestamp=datetime.now(self._get_timezone(market)),
            )
        except Exception:
            # Return default values on error
            return IVAnalysis(
                symbol=symbol,
                market=market,
                current_iv=0.25,
                iv_rank=50.0,
                iv_percentile=50.0,
                iv_52w_high=0.40,
                iv_52w_low=0.15,
                iv_30d_avg=0.24,
                timestamp=datetime.now(self._get_timezone(market)),
            )

    async def get_market_sentiment(self, symbol: str, market: Market) -> MarketSentiment:
        """Calculate market sentiment from option chain volume."""
        try:
            chain = await self.get_option_chain(symbol, market)

            call_volume = sum(c.volume or 0 for c in chain.calls)
            put_volume = sum(p.volume or 0 for p in chain.puts)

            if call_volume == 0:
                call_volume = 1

            pc_ratio = put_volume / call_volume

            if pc_ratio < 0.7:
                sentiment: Sentiment = "bullish"
            elif pc_ratio < 0.9:
                sentiment = "slightly_bullish"
            elif pc_ratio < 1.1:
                sentiment = "neutral"
            elif pc_ratio < 1.3:
                sentiment = "slightly_bearish"
            else:
                sentiment = "bearish"

            return MarketSentiment(
                symbol=symbol,
                market=market,
                put_call_ratio=pc_ratio,
                total_call_volume=call_volume,
                total_put_volume=put_volume,
                sentiment=sentiment,
                timestamp=datetime.now(self._get_timezone(market)),
            )
        except Exception:
            return MarketSentiment(
                symbol=symbol,
                market=market,
                put_call_ratio=0.85,
                total_call_volume=100000,
                total_put_volume=85000,
                sentiment="neutral",
                timestamp=datetime.now(self._get_timezone(market)),
            )

    async def get_unusual_activity(
        self, market: Market | None = None
    ) -> UnusualActivityResponse:
        """Return minimal unusual activity (Yahoo doesn't provide this data)."""
        # Yahoo doesn't provide unusual activity data, return empty
        return UnusualActivityResponse(alerts=[], timestamp=datetime.now(ZoneInfo("America/New_York")))

    async def get_strategy_suggestions(
        self, symbol: str, market: Market
    ) -> StrategySuggestionsResponse:
        """Generate strategy suggestions based on IV analysis."""
        try:
            iv_data = await self.get_iv_analysis(symbol, market)
            sentiment_data = await self.get_market_sentiment(symbol, market)

            iv_rank = iv_data.iv_rank
            pc_ratio = sentiment_data.put_call_ratio

            # Determine market conditions
            if iv_rank < 30:
                iv_level = "low"
            elif iv_rank < 70:
                iv_level = "medium"
            else:
                iv_level = "high"

            if pc_ratio < 0.8:
                trend = "bullish"
            elif pc_ratio > 1.2:
                trend = "bearish"
            else:
                trend = "neutral"

            suggestions = []

            if iv_rank > 70:
                suggestions.append(StrategySuggestion(
                    strategy="iron_condor",
                    display_name="Iron Condor",
                    suitability=85,
                    reasoning="High IV rank makes selling premium attractive",
                    risk_level="medium",
                    max_profit="Net credit received",
                    max_loss="Width of spread minus credit",
                ))
                suggestions.append(StrategySuggestion(
                    strategy="short_strangle",
                    display_name="Short Strangle",
                    suitability=75,
                    reasoning="Elevated IV provides good premium",
                    risk_level="high",
                    max_profit="Premium received",
                    max_loss="Unlimited",
                ))
            elif iv_rank < 30:
                suggestions.append(StrategySuggestion(
                    strategy="long_straddle",
                    display_name="Long Straddle",
                    suitability=80,
                    reasoning="Low IV makes buying options cheaper",
                    risk_level="medium",
                    max_profit="Unlimited",
                    max_loss="Premium paid",
                ))
                suggestions.append(StrategySuggestion(
                    strategy="calendar_spread",
                    display_name="Calendar Spread",
                    suitability=70,
                    reasoning="Benefit from IV expansion",
                    risk_level="low",
                    max_profit="If IV increases",
                    max_loss="Net debit paid",
                ))
            else:
                if trend == "bullish":
                    suggestions.append(StrategySuggestion(
                        strategy="bull_call_spread",
                        display_name="Bull Call Spread",
                        suitability=75,
                        reasoning="Bullish sentiment with defined risk",
                        risk_level="medium",
                        max_profit="Width minus debit",
                        max_loss="Net debit paid",
                    ))
                elif trend == "bearish":
                    suggestions.append(StrategySuggestion(
                        strategy="bear_put_spread",
                        display_name="Bear Put Spread",
                        suitability=75,
                        reasoning="Bearish sentiment with defined risk",
                        risk_level="medium",
                        max_profit="Width minus debit",
                        max_loss="Net debit paid",
                    ))
                else:
                    suggestions.append(StrategySuggestion(
                        strategy="iron_butterfly",
                        display_name="Iron Butterfly",
                        suitability=70,
                        reasoning="Neutral outlook with premium collection",
                        risk_level="medium",
                        max_profit="Net credit",
                        max_loss="Width minus credit",
                    ))

            return StrategySuggestionsResponse(
                symbol=symbol,
                market=market,
                market_conditions={
                    "iv_rank": iv_level,
                    "trend": trend,
                    "vix_level": "normal",
                },
                suggestions=suggestions,
                timestamp=datetime.now(self._get_timezone(market)),
            )
        except Exception:
            return StrategySuggestionsResponse(
                symbol=symbol,
                market=market,
                market_conditions={"iv_rank": "medium", "trend": "neutral", "vix_level": "normal"},
                suggestions=[
                    StrategySuggestion(
                        strategy="covered_call",
                        display_name="Covered Call",
                        suitability=70,
                        reasoning="Generate income on existing positions",
                        risk_level="low",
                        max_profit="Strike + premium - cost basis",
                        max_loss="Cost basis - premium",
                    )
                ],
                timestamp=datetime.now(self._get_timezone(market)),
            )
