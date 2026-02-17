"""Mock data provider for testing and development."""

import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from mcp_server.models import (
    Greeks,
    IVAnalysis,
    Market,
    MarketConditions,
    MarketSentiment,
    OptionChain,
    OptionContract,
    PriceBar,
    PriceHistory,
    Quote,
    StrategySuggestion,
    StrategySuggestionsResponse,
    UnusualActivityAlert,
    UnusualActivityResponse,
    VolatilitySurface,
)
from mcp_server.providers.base import MarketDataProvider


# Sample data for mock responses
MOCK_STOCKS = {
    "US": {
        "AAPL": {"name": "Apple Inc.", "price": 185.50},
        "MSFT": {"name": "Microsoft Corporation", "price": 378.25},
        "GOOGL": {"name": "Alphabet Inc.", "price": 141.80},
        "NVDA": {"name": "NVIDIA Corporation", "price": 495.20},
        "SPY": {"name": "SPDR S&P 500 ETF", "price": 478.50},
        "QQQ": {"name": "Invesco QQQ Trust", "price": 412.30},
        "DIA": {"name": "SPDR Dow Jones ETF", "price": 385.75},
        "IWM": {"name": "iShares Russell 2000 ETF", "price": 198.40},
        "VIX": {"name": "CBOE Volatility Index", "price": 18.45},
    },
    "JP": {
        "7203.T": {"name": "Toyota Motor Corp", "price": 2850.0},
        "9984.T": {"name": "SoftBank Group", "price": 8250.0},
        "6758.T": {"name": "Sony Group Corp", "price": 12500.0},
        "NKY": {"name": "Nikkei 225", "price": 38450.0},
    },
    "HK": {
        "0700.HK": {"name": "Tencent Holdings", "price": 375.40},
        "9988.HK": {"name": "Alibaba Group", "price": 78.25},
        "1299.HK": {"name": "AIA Group", "price": 62.50},
        "HSI": {"name": "Hang Seng Index", "price": 17680.0},
    },
}


class MockProvider(MarketDataProvider):
    """Mock provider returning simulated market data."""

    name = "mock"
    supported_markets: list[Market] = ["US", "JP", "HK"]

    def _get_timezone(self, market: Market) -> ZoneInfo:
        tzmap = {
            "US": ZoneInfo("America/New_York"),
            "JP": ZoneInfo("Asia/Tokyo"),
            "HK": ZoneInfo("Asia/Hong_Kong"),
        }
        return tzmap[market]

    def _add_noise(self, price: float, pct: float = 0.001) -> float:
        """Add small random noise to price."""
        return price * (1 + random.uniform(-pct, pct))

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Return mock quote data."""
        stocks = MOCK_STOCKS.get(market, {})
        stock = stocks.get(symbol)

        if stock:
            base_price = stock["price"]
        else:
            base_price = 100.0

        price = self._add_noise(base_price)
        spread = price * 0.001

        # Simulate daily change (-2% to +2%)
        change_percent = random.uniform(-2.0, 2.0)
        change = round(base_price * change_percent / 100, 2)

        return Quote(
            symbol=symbol,
            market=market,
            price=round(price, 2),
            change=change,
            change_percent=round(change_percent, 2),
            bid=round(price - spread, 2),
            ask=round(price + spread, 2),
            volume=random.randint(100000, 5000000),
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Return mock option chain."""
        quote = await self.get_quote(symbol, market)
        underlying_price = quote.price

        # Generate expirations (weekly for next month, monthly for 3 months)
        today = date.today()
        expirations = []
        for i in range(1, 5):
            expirations.append(today + timedelta(days=7 * i))
        for i in range(1, 4):
            expirations.append(today + timedelta(days=30 * i))
        expirations = sorted(set(expirations))

        if expiration:
            exp_date = date.fromisoformat(expiration)
            expirations = [exp_date] if exp_date in expirations else [expirations[0]]

        # Generate strikes around current price
        strike_step = underlying_price * 0.025
        strikes = [
            round(underlying_price + (i * strike_step), 2)
            for i in range(-5, 6)
        ]

        calls = []
        puts = []

        for exp in expirations:
            days_to_exp = (exp - today).days
            for strike in strikes:
                moneyness = (underlying_price - strike) / underlying_price
                base_iv = 0.25 + abs(moneyness) * 0.5 + random.uniform(-0.02, 0.02)

                # Call option
                call_price = max(0.01, (underlying_price - strike) + base_iv * underlying_price * 0.1)
                calls.append(
                    OptionContract(
                        symbol=f"{symbol}{exp.strftime('%y%m%d')}C{int(strike*1000):08d}",
                        underlying=symbol,
                        strike=strike,
                        expiration=exp,
                        option_type="call",
                        bid=round(call_price * 0.98, 2),
                        ask=round(call_price * 1.02, 2),
                        last_price=round(call_price, 2),
                        volume=random.randint(10, 1000),
                        open_interest=random.randint(100, 10000),
                        implied_volatility=round(base_iv, 4),
                        greeks=Greeks(
                            delta=round(0.5 + moneyness * 2, 4),
                            gamma=round(0.05 * (1 - abs(moneyness)), 4),
                            theta=round(-0.05 * base_iv * underlying_price / 365, 4),
                            vega=round(0.01 * underlying_price * (days_to_exp / 365) ** 0.5, 4),
                            rho=round(0.01 * strike * days_to_exp / 365, 4),
                        ),
                    )
                )

                # Put option
                put_price = max(0.01, (strike - underlying_price) + base_iv * underlying_price * 0.1)
                puts.append(
                    OptionContract(
                        symbol=f"{symbol}{exp.strftime('%y%m%d')}P{int(strike*1000):08d}",
                        underlying=symbol,
                        strike=strike,
                        expiration=exp,
                        option_type="put",
                        bid=round(put_price * 0.98, 2),
                        ask=round(put_price * 1.02, 2),
                        last_price=round(put_price, 2),
                        volume=random.randint(10, 1000),
                        open_interest=random.randint(100, 10000),
                        implied_volatility=round(base_iv, 4),
                        greeks=Greeks(
                            delta=round(-0.5 + moneyness * 2, 4),
                            gamma=round(0.05 * (1 - abs(moneyness)), 4),
                            theta=round(-0.05 * base_iv * underlying_price / 365, 4),
                            vega=round(0.01 * underlying_price * (days_to_exp / 365) ** 0.5, 4),
                            rho=round(-0.01 * strike * days_to_exp / 365, 4),
                        ),
                    )
                )

        return OptionChain(
            underlying=symbol,
            market=market,
            expirations=expirations,
            calls=calls,
            puts=puts,
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_volatility_surface(
        self,
        symbol: str,
        market: Market,
    ) -> VolatilitySurface:
        """Return mock volatility surface."""
        quote = await self.get_quote(symbol, market)
        underlying_price = quote.price

        today = date.today()
        expirations = [today + timedelta(days=d) for d in [7, 14, 30, 60, 90, 180]]

        strike_step = underlying_price * 0.05
        strikes = [round(underlying_price + (i * strike_step), 2) for i in range(-4, 5)]

        call_ivs = []
        put_ivs = []

        for exp in expirations:
            days = (exp - today).days
            term_factor = 1 + 0.1 * (30 / max(days, 1))

            call_row = []
            put_row = []
            for strike in strikes:
                moneyness = (strike - underlying_price) / underlying_price
                skew = 0.05 * moneyness  # Slight skew
                base_iv = 0.20 * term_factor + abs(moneyness) * 0.3

                call_row.append(round(base_iv - skew + random.uniform(-0.01, 0.01), 4))
                put_row.append(round(base_iv + skew + random.uniform(-0.01, 0.01), 4))

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
        """Return mock historical price data."""
        stocks = MOCK_STOCKS.get(market, {})
        stock = stocks.get(symbol)
        base_price = stock["price"] if stock else 100.0

        tz = self._get_timezone(market)
        now = datetime.now(tz)
        bars = []

        # Generate bars going backwards in time
        for i in range(limit - 1, -1, -1):
            if interval == "1d":
                bar_time = now - timedelta(days=i)
            elif interval == "1h":
                bar_time = now - timedelta(hours=i)
            else:  # 5m
                bar_time = now - timedelta(minutes=i * 5)

            # Create realistic price movement with trend and volatility
            trend = (limit - i) / limit * random.uniform(-0.05, 0.15)  # Slight upward bias
            daily_volatility = random.uniform(-0.02, 0.02)
            price_factor = 1 + trend + daily_volatility

            close = round(base_price * price_factor, 2)
            intraday_range = close * random.uniform(0.005, 0.02)
            open_price = round(close + random.uniform(-intraday_range, intraday_range), 2)
            high = round(max(open_price, close) + random.uniform(0, intraday_range), 2)
            low = round(min(open_price, close) - random.uniform(0, intraday_range), 2)

            bars.append(PriceBar(
                timestamp=bar_time,
                open=open_price,
                high=high,
                low=low,
                close=close,
                volume=random.randint(500000, 5000000),
            ))

        return PriceHistory(
            symbol=symbol,
            market=market,
            interval=interval,
            bars=bars,
        )

    # Dashboard methods

    async def get_iv_analysis(
        self,
        symbol: str,
        market: Market,
    ) -> IVAnalysis:
        """Return mock IV analysis data."""
        # Generate realistic IV values
        base_iv = random.uniform(0.15, 0.45)
        iv_52w_high = base_iv * random.uniform(1.3, 2.0)
        iv_52w_low = base_iv * random.uniform(0.4, 0.7)

        current_iv = random.uniform(iv_52w_low, iv_52w_high)

        # Calculate IV rank: where current IV falls in the 52-week range
        iv_range = iv_52w_high - iv_52w_low
        iv_rank = ((current_iv - iv_52w_low) / iv_range) * 100 if iv_range > 0 else 50

        # IV percentile: percentage of days with lower IV (simulated)
        iv_percentile = iv_rank + random.uniform(-10, 10)
        iv_percentile = max(0, min(100, iv_percentile))

        return IVAnalysis(
            symbol=symbol,
            market=market,
            current_iv=round(current_iv, 4),
            iv_rank=round(iv_rank, 1),
            iv_percentile=round(iv_percentile, 1),
            iv_52w_high=round(iv_52w_high, 4),
            iv_52w_low=round(iv_52w_low, 4),
            iv_30d_avg=round((current_iv + base_iv) / 2, 4),
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_market_sentiment(
        self,
        symbol: str,
        market: Market,
    ) -> MarketSentiment:
        """Return mock market sentiment data."""
        # Generate realistic put/call volumes
        total_call_volume = random.randint(500000, 3000000)
        put_call_ratio = random.uniform(0.5, 1.5)
        total_put_volume = int(total_call_volume * put_call_ratio)

        call_oi = random.randint(2000000, 10000000)
        put_oi = int(call_oi * random.uniform(0.7, 1.3))

        # Determine sentiment based on P/C ratio
        if put_call_ratio < 0.7:
            sentiment = "bullish"
        elif put_call_ratio < 0.85:
            sentiment = "slightly_bullish"
        elif put_call_ratio <= 1.15:
            sentiment = "neutral"
        elif put_call_ratio <= 1.3:
            sentiment = "slightly_bearish"
        else:
            sentiment = "bearish"

        return MarketSentiment(
            symbol=symbol,
            market=market,
            put_call_ratio=round(put_call_ratio, 2),
            total_call_volume=total_call_volume,
            total_put_volume=total_put_volume,
            call_open_interest=call_oi,
            put_open_interest=put_oi,
            sentiment=sentiment,
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_unusual_activity(
        self,
        market: Market | None = None,
    ) -> UnusualActivityResponse:
        """Return mock unusual activity alerts."""
        alerts = []
        tz = self._get_timezone(market or "US")

        # Generate some random alerts
        alert_types = ["volume_spike", "unusual_pc_ratio", "oi_change"]
        symbols_to_check = []

        if market:
            symbols_to_check = list(MOCK_STOCKS.get(market, {}).keys())
        else:
            for m, stocks in MOCK_STOCKS.items():
                for s in stocks.keys():
                    symbols_to_check.append((s, m))

        # Generate 3-7 random alerts
        num_alerts = random.randint(3, 7)
        for _ in range(num_alerts):
            if market:
                sym = random.choice(symbols_to_check) if symbols_to_check else "AAPL"
                mkt = market
            else:
                if symbols_to_check:
                    sym, mkt = random.choice(symbols_to_check)
                else:
                    sym, mkt = "AAPL", "US"

            alert_type = random.choice(alert_types)
            significance = round(random.uniform(5, 10), 1)

            if alert_type == "volume_spike":
                multiplier = round(random.uniform(2, 5), 1)
                description = f"Call volume {multiplier}x above 20-day average"
                details = {
                    "current_volume": random.randint(50000, 200000),
                    "avg_volume": random.randint(15000, 40000),
                    "option_type": random.choice(["call", "put"]),
                    "strike": round(random.uniform(150, 200), 0),
                }
            elif alert_type == "unusual_pc_ratio":
                ratio = round(random.uniform(0.3, 0.6) if random.random() > 0.5 else random.uniform(1.6, 2.5), 2)
                description = f"Unusual P/C ratio of {ratio}"
                details = {
                    "put_call_ratio": ratio,
                    "call_volume": random.randint(100000, 500000),
                    "put_volume": random.randint(100000, 500000),
                }
            else:  # oi_change
                pct_change = round(random.uniform(15, 50), 1)
                description = f"Open interest increased {pct_change}% day-over-day"
                details = {
                    "oi_change_pct": pct_change,
                    "current_oi": random.randint(50000, 200000),
                    "previous_oi": random.randint(30000, 150000),
                }

            alerts.append(UnusualActivityAlert(
                symbol=sym,
                market=mkt,
                alert_type=alert_type,
                description=description,
                significance=significance,
                details=details,
                timestamp=datetime.now(tz) - timedelta(minutes=random.randint(5, 120)),
            ))

        # Sort by significance descending
        alerts.sort(key=lambda x: x.significance, reverse=True)

        return UnusualActivityResponse(alerts=alerts)

    async def get_strategy_suggestions(
        self,
        symbol: str,
        market: Market,
    ) -> StrategySuggestionsResponse:
        """Return mock strategy suggestions."""
        # Get IV analysis to base suggestions on
        iv_data = await self.get_iv_analysis(symbol, market)

        # Determine market conditions
        if iv_data.iv_rank > 70:
            iv_level = "high"
        elif iv_data.iv_rank > 30:
            iv_level = "medium"
        else:
            iv_level = "low"

        vix_level = random.choice(["low", "normal", "elevated", "high"])
        trend = random.choice(["bullish", "slightly_bullish", "neutral", "slightly_bearish", "bearish"])
        vol_outlook = random.choice(["increasing", "stable", "decreasing"])

        conditions = MarketConditions(
            vix_level=vix_level,
            iv_rank=iv_level,
            trend=trend,
            volatility_outlook=vol_outlook,
        )

        # Generate strategy suggestions based on conditions
        suggestions = []

        # High IV strategies (sell premium)
        if iv_level == "high":
            suggestions.append(StrategySuggestion(
                strategy="iron_condor",
                display_name="Iron Condor",
                suitability=85 + random.randint(-5, 5),
                reasoning="High IV rank suggests selling premium; collect elevated premiums while betting on range-bound price action",
                risk_level="medium",
                max_profit="Net credit received",
                max_loss="Width of spread minus credit",
            ))
            suggestions.append(StrategySuggestion(
                strategy="short_strangle",
                display_name="Short Strangle",
                suitability=75 + random.randint(-5, 5),
                reasoning="Elevated IV makes selling options attractive; profit from time decay if stock stays within range",
                risk_level="high",
                max_profit="Total premium collected",
                max_loss="Unlimited",
            ))
            suggestions.append(StrategySuggestion(
                strategy="credit_spread",
                display_name="Credit Spread",
                suitability=80 + random.randint(-5, 5),
                reasoning="High IV allows for wider spreads with good risk/reward; defined risk strategy",
                risk_level="medium",
                max_profit="Net credit received",
                max_loss="Width of spread minus credit",
            ))

        # Low IV strategies (buy premium)
        elif iv_level == "low":
            suggestions.append(StrategySuggestion(
                strategy="long_straddle",
                display_name="Long Straddle",
                suitability=80 + random.randint(-5, 5),
                reasoning="Low IV means cheaper options; profit from any large move in either direction",
                risk_level="medium",
                max_profit="Unlimited",
                max_loss="Total premium paid",
            ))
            suggestions.append(StrategySuggestion(
                strategy="calendar_spread",
                display_name="Calendar Spread",
                suitability=75 + random.randint(-5, 5),
                reasoning="Buy cheap longer-dated options, sell expensive near-term; benefit when IV expands",
                risk_level="low",
                max_profit="Varies with IV expansion",
                max_loss="Net debit paid",
            ))

        # Directional strategies based on trend
        if trend in ["bullish", "slightly_bullish"]:
            suggestions.append(StrategySuggestion(
                strategy="bull_call_spread",
                display_name="Bull Call Spread",
                suitability=70 + random.randint(-5, 10),
                reasoning=f"{trend.replace('_', ' ').title()} trend suggests upside potential; limited risk bullish position",
                risk_level="low",
                max_profit="Width of spread minus debit",
                max_loss="Net debit paid",
            ))
        elif trend in ["bearish", "slightly_bearish"]:
            suggestions.append(StrategySuggestion(
                strategy="bear_put_spread",
                display_name="Bear Put Spread",
                suitability=70 + random.randint(-5, 10),
                reasoning=f"{trend.replace('_', ' ').title()} trend indicates downside risk; profit from decline with limited risk",
                risk_level="low",
                max_profit="Width of spread minus debit",
                max_loss="Net debit paid",
            ))

        # Neutral strategy
        if trend == "neutral":
            suggestions.append(StrategySuggestion(
                strategy="butterfly",
                display_name="Butterfly Spread",
                suitability=75 + random.randint(-5, 5),
                reasoning="Neutral outlook with low cost entry; maximum profit if stock pins at center strike",
                risk_level="low",
                max_profit="Width of spread minus debit",
                max_loss="Net debit paid",
            ))

        # Sort by suitability
        suggestions.sort(key=lambda x: x.suitability, reverse=True)

        return StrategySuggestionsResponse(
            symbol=symbol,
            market=market,
            market_conditions=conditions,
            suggestions=suggestions[:4],  # Return top 4
            timestamp=datetime.now(self._get_timezone(market)),
        )
