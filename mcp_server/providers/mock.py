"""Mock data provider for testing and development."""

import random
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from mcp_server.models import (
    Greeks,
    Market,
    OptionChain,
    OptionContract,
    Quote,
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
    },
    "JP": {
        "7203.T": {"name": "Toyota Motor Corp", "price": 2850.0},
        "9984.T": {"name": "SoftBank Group", "price": 8250.0},
        "6758.T": {"name": "Sony Group Corp", "price": 12500.0},
    },
    "HK": {
        "0700.HK": {"name": "Tencent Holdings", "price": 375.40},
        "9988.HK": {"name": "Alibaba Group", "price": 78.25},
        "1299.HK": {"name": "AIA Group", "price": 62.50},
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

        return Quote(
            symbol=symbol,
            market=market,
            price=round(price, 2),
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
