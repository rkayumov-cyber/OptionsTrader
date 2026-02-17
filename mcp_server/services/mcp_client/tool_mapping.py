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
        """Parse quote from Yahoo or Alpha Vantage format."""
        if not data:
            return None

        # AV TOOL_CALL returns CSV string for GLOBAL_QUOTE
        if isinstance(data, str) and "price" in data and "," in data:
            parsed = _parse_csv_row(data)
            if parsed:
                return ToolMapper._parse_av_quote(parsed, symbol, market)
            return None

        if not isinstance(data, dict):
            return None

        # Detect Alpha Vantage JSON format: {"Global Quote": {"01. symbol": ...}}
        if "Global Quote" in data:
            return ToolMapper._parse_av_quote(data["Global Quote"], symbol, market)

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
    def _parse_av_quote(gq: dict, symbol: str, market: Market) -> Quote | None:
        """Alpha Vantage Global Quote -> Quote.

        Handles both JSON format (numbered keys like "05. price")
        and CSV-parsed format (simple keys like "price").
        """
        try:
            # Try CSV-parsed format first (simple keys), then JSON format (numbered keys)
            price = float(gq.get("price") or gq.get("05. price", 0))
            change = _safe_float(gq.get("change") or gq.get("09. change"))
            change_pct_str = gq.get("changePercent") or gq.get("10. change percent", "0%")
            change_pct = _safe_float(change_pct_str.rstrip("%")) if isinstance(change_pct_str, str) else _safe_float(change_pct_str)
            volume = int(float(gq.get("volume") or gq.get("06. volume", 0)))

            if price <= 0:
                return None

            return Quote(
                symbol=symbol,
                market=market,
                price=price,
                change=change,
                change_percent=change_pct,
                bid=None,
                ask=None,
                volume=volume,
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error("Failed to parse AV quote for %s: %s", symbol, e)
            return None

    @staticmethod
    def parse_price_history(
        data: Any, symbol: str, market: Market, interval: str = "1d"
    ) -> PriceHistory | None:
        """Parse price history from Yahoo or Alpha Vantage format."""
        if not data:
            return None

        # AV TOOL_CALL may return CSV string for time series
        if isinstance(data, str) and "timestamp" in data.lower() and "," in data:
            return ToolMapper._parse_av_time_series_csv(data, symbol, market, interval)

        # Detect AV Time Series JSON: {"Time Series (Daily)": {"2025-02-14": {...}}}
        if isinstance(data, dict):
            for key in data:
                if "Time Series" in key:
                    return ToolMapper._parse_av_time_series(data[key], symbol, market, interval)

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
    def _parse_av_time_series(
        ts_data: dict, symbol: str, market: Market, interval: str
    ) -> PriceHistory | None:
        """Alpha Vantage Time Series -> PriceHistory."""
        try:
            bars = []
            for date_str, values in sorted(ts_data.items()):
                ts = datetime.fromisoformat(date_str) if "T" in date_str else datetime.strptime(date_str, "%Y-%m-%d")
                bars.append(
                    PriceBar(
                        timestamp=ts,
                        open=float(values.get("1. open", 0)),
                        high=float(values.get("2. high", 0)),
                        low=float(values.get("3. low", 0)),
                        close=float(values.get("4. close", 0)),
                        volume=int(float(values.get("5. volume", 0))),
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
            logger.error("Failed to parse AV time series for %s: %s", symbol, e)
            return None

    @staticmethod
    def _parse_av_time_series_csv(
        csv_text: str, symbol: str, market: Market, interval: str
    ) -> PriceHistory | None:
        """Parse AV time series CSV (multi-row) into PriceHistory."""
        try:
            lines = [l.strip() for l in csv_text.strip().splitlines() if l.strip()]
            if len(lines) < 2:
                return None
            headers = [h.strip().lower() for h in lines[0].split(",")]
            bars = []
            for line in lines[1:]:
                vals = [v.strip() for v in line.split(",")]
                row = dict(zip(headers, vals))
                ts_str = row.get("timestamp") or row.get("date") or row.get("time")
                if not ts_str:
                    continue
                ts = datetime.fromisoformat(ts_str) if "T" in ts_str else datetime.strptime(ts_str, "%Y-%m-%d")
                bars.append(
                    PriceBar(
                        timestamp=ts,
                        open=float(row.get("open", 0)),
                        high=float(row.get("high", 0)),
                        low=float(row.get("low", 0)),
                        close=float(row.get("close", 0)),
                        volume=int(float(row.get("volume", 0))),
                    )
                )
            if not bars:
                return None
            return PriceHistory(symbol=symbol, market=market, interval=interval, bars=bars)
        except Exception as e:
            logger.error("Failed to parse AV time series CSV for %s: %s", symbol, e)
            return None

    @staticmethod
    def parse_market_sentiment(
        data: Any, symbol: str, market: Market
    ) -> MarketSentiment | None:
        """Parse sentiment from Yahoo recommendations or AV NEWS_SENTIMENT."""
        if not data:
            return None

        # Detect Alpha Vantage NEWS_SENTIMENT format (JSON with "feed" key)
        if isinstance(data, dict) and "feed" in data:
            return ToolMapper._parse_av_sentiment(data, symbol, market)

        # AV NEWS_SENTIMENT can also return CSV with sentiment scores
        if isinstance(data, str) and "overall_sentiment_score" in data:
            return ToolMapper._parse_av_sentiment_csv(data, symbol, market)

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
    def _parse_av_sentiment(
        data: dict, symbol: str, market: Market
    ) -> MarketSentiment | None:
        """Alpha Vantage NEWS_SENTIMENT feed -> MarketSentiment."""
        try:
            feed = data.get("feed", [])
            if not feed:
                return None

            bullish = 0
            bearish = 0
            neutral = 0

            for article in feed:
                # Look for ticker-specific sentiment
                ticker_sentiments = article.get("ticker_sentiment", [])
                for ts in ticker_sentiments:
                    if ts.get("ticker", "").upper() == symbol.upper():
                        score = float(ts.get("ticker_sentiment_score", 0))
                        if score > 0.15:
                            bullish += 1
                        elif score < -0.15:
                            bearish += 1
                        else:
                            neutral += 1
                        break
                else:
                    # Use overall sentiment if ticker-specific not found
                    score = float(article.get("overall_sentiment_score", 0))
                    if score > 0.15:
                        bullish += 1
                    elif score < -0.15:
                        bearish += 1
                    else:
                        neutral += 1

            total = bullish + bearish + neutral
            if total == 0:
                total = 1

            call_vol = bullish * 10000 + neutral * 5000
            put_vol = bearish * 10000 + neutral * 5000
            pc_ratio = put_vol / max(call_vol, 1)

            bullish_pct = bullish / total
            if bullish_pct > 0.6:
                sentiment = "bullish"
            elif bullish_pct > 0.45:
                sentiment = "slightly_bullish"
            elif bullish_pct > 0.3:
                sentiment = "neutral"
            elif bullish_pct > 0.15:
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
            logger.error("Failed to parse AV sentiment for %s: %s", symbol, e)
            return None

    @staticmethod
    def _parse_av_sentiment_csv(
        csv_text: str, symbol: str, market: Market
    ) -> MarketSentiment | None:
        """Parse AV NEWS_SENTIMENT CSV into MarketSentiment."""
        try:
            lines = [l.strip() for l in csv_text.strip().splitlines() if l.strip()]
            if len(lines) < 2:
                return None
            headers = [h.strip().lower() for h in lines[0].split(",")]
            bullish = bearish = neutral = 0
            for line in lines[1:]:
                vals = [v.strip() for v in line.split(",")]
                row = dict(zip(headers, vals))
                score = float(row.get("overall_sentiment_score", 0))
                if score > 0.15:
                    bullish += 1
                elif score < -0.15:
                    bearish += 1
                else:
                    neutral += 1
            total = bullish + bearish + neutral or 1
            call_vol = bullish * 10000 + neutral * 5000
            put_vol = bearish * 10000 + neutral * 5000
            pc_ratio = put_vol / max(call_vol, 1)
            bullish_pct = bullish / total
            if bullish_pct > 0.6:
                sentiment = "bullish"
            elif bullish_pct > 0.45:
                sentiment = "slightly_bullish"
            elif bullish_pct > 0.3:
                sentiment = "neutral"
            elif bullish_pct > 0.15:
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
            logger.error("Failed to parse AV sentiment CSV for %s: %s", symbol, e)
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


def _parse_csv_row(csv_text: str) -> dict | None:
    """Parse a 2-line CSV (header + single data row) into a dict."""
    lines = [l.strip() for l in csv_text.strip().splitlines() if l.strip()]
    if len(lines) < 2:
        return None
    headers = [h.strip() for h in lines[0].split(",")]
    values = [v.strip() for v in lines[1].split(",")]
    if len(headers) != len(values):
        return None
    return dict(zip(headers, values))


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
