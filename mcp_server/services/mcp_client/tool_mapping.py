"""ToolMapper - translates MCP tool responses to internal Pydantic models."""

import logging
from datetime import datetime, date
from typing import Any

from mcp_server.models import (
    IVAnalysis,
    Market,
    MarketSentiment,
    OptionChain,
    OptionContract,
    PriceBar,
    PriceHistory,
    Quote,
)

logger = logging.getLogger(__name__)


class ToolMapper:
    """Normalizes diverse MCP server responses into internal Pydantic models."""

    @staticmethod
    def parse_quote(data: Any, symbol: str, market: Market) -> Quote | None:
        """Yahoo get_stock_info JSON -> Quote."""
        if not data or not isinstance(data, dict):
            return None

        try:
            price = (
                data.get("currentPrice")
                or data.get("regularMarketPrice")
                or data.get("price")
                or 0.0
            )
            change = data.get("regularMarketChange") or data.get("change")
            change_pct = data.get("regularMarketChangePercent") or data.get(
                "changePercent"
            )

            return Quote(
                symbol=symbol,
                market=market,
                price=float(price),
                change=float(change) if change is not None else None,
                change_percent=float(change_pct) if change_pct is not None else None,
                bid=_safe_float(data.get("bid")),
                ask=_safe_float(data.get("ask")),
                volume=int(data.get("volume") or data.get("regularMarketVolume") or 0),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to parse quote for %s: %s", symbol, e)
            return None

    @staticmethod
    def parse_price_history(
        data: Any, symbol: str, market: Market, interval: str = "1d"
    ) -> PriceHistory | None:
        """Yahoo get_historical_stock_prices JSON -> PriceHistory."""
        if not data:
            return None

        try:
            bars_data = data if isinstance(data, list) else data.get("prices", [])
            bars = []
            for bar in bars_data:
                if not isinstance(bar, dict):
                    continue
                ts = bar.get("date") or bar.get("timestamp")
                if isinstance(ts, (int, float)):
                    ts = datetime.fromtimestamp(ts)
                elif isinstance(ts, str):
                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                else:
                    ts = datetime.now()

                bars.append(
                    PriceBar(
                        timestamp=ts,
                        open=float(bar.get("open", 0)),
                        high=float(bar.get("high", 0)),
                        low=float(bar.get("low", 0)),
                        close=float(bar.get("close", 0)),
                        volume=int(bar.get("volume", 0)),
                    )
                )

            if not bars:
                return None

            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=bars,
            )
        except Exception as e:
            logger.error("Failed to parse price history for %s: %s", symbol, e)
            return None

    @staticmethod
    def parse_market_sentiment(
        data: Any, symbol: str, market: Market
    ) -> MarketSentiment | None:
        """Yahoo get_recommendations JSON -> MarketSentiment."""
        if not data:
            return None

        try:
            # Yahoo recommendations returns analyst sentiments
            # We map this to our MarketSentiment model
            recommendations = data if isinstance(data, list) else data.get("recommendations", [data])

            # Count buy/sell signals to derive sentiment
            buy_count = 0
            sell_count = 0
            hold_count = 0

            for rec in recommendations:
                if not isinstance(rec, dict):
                    continue
                # Yahoo format varies - check multiple fields
                grade = (
                    rec.get("recommendationKey", "")
                    or rec.get("toGrade", "")
                    or rec.get("rating", "")
                ).lower()
                if any(k in grade for k in ["buy", "overweight", "outperform", "strong_buy"]):
                    buy_count += 1
                elif any(k in grade for k in ["sell", "underweight", "underperform"]):
                    sell_count += 1
                else:
                    hold_count += 1

            total = buy_count + sell_count + hold_count
            if total == 0:
                total = 1

            # Derive put/call-like ratio from analyst sentiment
            # More sells = higher "put" pressure, more buys = higher "call" pressure
            call_vol = buy_count * 10000 + hold_count * 5000
            put_vol = sell_count * 10000 + hold_count * 5000
            pc_ratio = put_vol / max(call_vol, 1)

            # Classify sentiment
            bullish_pct = buy_count / total
            if bullish_pct > 0.7:
                sentiment = "bullish"
            elif bullish_pct > 0.55:
                sentiment = "slightly_bullish"
            elif bullish_pct > 0.4:
                sentiment = "neutral"
            elif bullish_pct > 0.25:
                sentiment = "slightly_bearish"
            else:
                sentiment = "bearish"

            return MarketSentiment(
                symbol=symbol,
                market=market,
                put_call_ratio=round(pc_ratio, 3),
                total_call_volume=call_vol,
                total_put_volume=put_vol,
                call_open_interest=call_vol * 10,
                put_open_interest=put_vol * 10,
                sentiment=sentiment,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to parse sentiment for %s: %s", symbol, e)
            return None

    @staticmethod
    def build_iv_analysis(
        data: Any, symbol: str, market: Market
    ) -> IVAnalysis | None:
        """Yahoo get_stock_info -> IVAnalysis.

        Derives implied volatility from 52-week price range as a proxy
        when the stock info doesn't contain an explicit IV field.
        """
        if not data or not isinstance(data, dict):
            return None

        try:
            current_iv = data.get("impliedVolatility") or data.get("iv")

            if current_iv is not None:
                current_iv = float(current_iv)
            elif "fiftyTwoWeekHigh" in data and "fiftyTwoWeekLow" in data:
                # Derive historical vol from 52-week range using Parkinson estimator
                price = float(data.get("currentPrice") or data.get("regularMarketPrice") or 0)
                high = float(data["fiftyTwoWeekHigh"])
                low = float(data["fiftyTwoWeekLow"])
                if price > 0 and high > low:
                    import math
                    current_iv = math.log(high / low) / math.sqrt(252 / 365) * 0.6
                    current_iv = max(0.05, min(2.0, current_iv))
                else:
                    return None
            else:
                return None

            # Estimate IV range from price movement
            high = float(data.get("fiftyTwoWeekHigh", 0))
            low = float(data.get("fiftyTwoWeekLow", 0))
            price = float(data.get("currentPrice") or data.get("regularMarketPrice") or 1)

            if high > 0 and low > 0:
                price_range = (high - low) / price
                iv_52w_high = max(current_iv, current_iv * (1 + price_range * 0.5))
                iv_52w_low = max(0.05, current_iv * (1 - price_range * 0.3))
            else:
                iv_52w_high = current_iv * 1.5
                iv_52w_low = current_iv * 0.5

            iv_range = iv_52w_high - iv_52w_low
            iv_rank = ((current_iv - iv_52w_low) / iv_range * 100) if iv_range > 0 else 50

            return IVAnalysis(
                symbol=symbol,
                market=market,
                current_iv=round(current_iv, 4),
                iv_rank=round(max(0, min(100, iv_rank)), 2),
                iv_percentile=round(max(0, min(100, iv_rank * 0.95)), 2),
                iv_52w_high=round(iv_52w_high, 4),
                iv_52w_low=round(iv_52w_low, 4),
                iv_30d_avg=round(current_iv * 0.95, 4),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to build IV analysis for %s: %s", symbol, e)
            return None

    @staticmethod
    def build_iv_from_chain(
        chain_data: Any, stock_data: Any, symbol: str, market: Market
    ) -> IVAnalysis | None:
        """Build IV analysis from option chain data (ATM IV)."""
        if not chain_data:
            return None

        try:
            contracts = chain_data if isinstance(chain_data, list) else chain_data.get("calls", chain_data.get("options", []))
            if not contracts:
                return None

            # Find ATM contract by looking at the one closest to current price
            price = 0.0
            if stock_data and isinstance(stock_data, dict):
                price = float(stock_data.get("currentPrice") or stock_data.get("regularMarketPrice") or 0)

            # Collect all IVs from contracts
            ivs = []
            for c in contracts:
                if not isinstance(c, dict):
                    continue
                iv = c.get("impliedVolatility")
                if iv is not None:
                    iv = float(iv)
                    if 0 < iv < 5:  # Sanity check
                        ivs.append((abs(float(c.get("strike", 0)) - price), iv))

            if not ivs:
                return None

            # Sort by distance to ATM, take median of closest 5
            ivs.sort(key=lambda x: x[0])
            closest = [iv for _, iv in ivs[:5]]
            current_iv = sorted(closest)[len(closest) // 2]  # Median

            iv_52w_high = current_iv * 1.5
            iv_52w_low = max(0.05, current_iv * 0.5)
            iv_range = iv_52w_high - iv_52w_low
            iv_rank = ((current_iv - iv_52w_low) / iv_range * 100) if iv_range > 0 else 50

            return IVAnalysis(
                symbol=symbol,
                market=market,
                current_iv=round(current_iv, 4),
                iv_rank=round(max(0, min(100, iv_rank)), 2),
                iv_percentile=round(max(0, min(100, iv_rank * 0.95)), 2),
                iv_52w_high=round(iv_52w_high, 4),
                iv_52w_low=round(iv_52w_low, 4),
                iv_30d_avg=round(current_iv * 0.95, 4),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to build IV from chain for %s: %s", symbol, e)
            return None

    @staticmethod
    def parse_option_chain(
        data: Any, symbol: str, market: Market
    ) -> OptionChain | None:
        """Yahoo get_option_chain JSON -> OptionChain."""
        if not data:
            return None

        try:
            calls_data = data.get("calls", [])
            puts_data = data.get("puts", [])

            def parse_contracts(contracts: list, opt_type: str) -> list[OptionContract]:
                result = []
                for c in contracts:
                    if not isinstance(c, dict):
                        continue
                    exp = c.get("expiration") or c.get("expirationDate", "")
                    if isinstance(exp, (int, float)):
                        exp = datetime.fromtimestamp(exp).date()
                    elif isinstance(exp, str):
                        exp = date.fromisoformat(exp[:10])
                    else:
                        continue

                    result.append(
                        OptionContract(
                            symbol=c.get("contractSymbol", f"{symbol}{exp}"),
                            underlying=symbol,
                            strike=float(c.get("strike", 0)),
                            expiration=exp,
                            option_type=opt_type,
                            bid=_safe_float(c.get("bid")),
                            ask=_safe_float(c.get("ask")),
                            last_price=_safe_float(c.get("lastPrice")),
                            volume=int(c.get("volume") or 0),
                            open_interest=int(c.get("openInterest") or 0),
                            implied_volatility=_safe_float(
                                c.get("impliedVolatility")
                            ),
                        )
                    )
                return result

            calls = parse_contracts(calls_data, "call")
            puts = parse_contracts(puts_data, "put")

            # Collect unique expirations
            all_exps = set()
            for c in calls + puts:
                all_exps.add(c.expiration)

            return OptionChain(
                underlying=symbol,
                market=market,
                expirations=sorted(all_exps),
                calls=calls,
                puts=puts,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to parse option chain for %s: %s", symbol, e)
            return None


def _safe_float(val: Any) -> float | None:
    """Safely convert to float, returning None for invalid values."""
    if val is None:
        return None
    try:
        f = float(val)
        if f != f:  # NaN check
            return None
        return f
    except (ValueError, TypeError):
        return None
