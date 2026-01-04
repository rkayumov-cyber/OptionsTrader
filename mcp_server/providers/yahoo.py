"""Yahoo Finance data provider."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import yfinance as yf

from mcp_server.models import (
    Greeks,
    Market,
    OptionChain,
    OptionContract,
    Quote,
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
