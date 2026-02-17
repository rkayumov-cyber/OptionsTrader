"""Interactive Brokers data provider using ib_insync.

All IB operations run synchronously in a dedicated thread to avoid
event-loop conflicts between ib_insync and FastAPI/uvicorn on Windows.
"""

import asyncio
import math
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ib_insync import Contract, IB, Index, Option, Stock

from mcp_server.models import (
    Greeks,
    Market,
    OptionChain,
    OptionContract,
    PriceBar,
    PriceHistory,
    Quote,
    VolatilitySurface,
)
from mcp_server.providers.base import MarketDataProvider

# Symbols that are indices (not stocks) and need Index contracts in IB.
# Maps frontend symbol -> (IB symbol, exchange, currency).
_INDEX_MAP: dict[str, tuple[str, str, str]] = {
    "VIX":  ("VIX",  "CBOE",    "USD"),
    "^VIX": ("VIX",  "CBOE",    "USD"),
    "^TNX": ("TNX",  "CBOE",    "USD"),
    "^IRX": ("IRX",  "CBOE",    "USD"),
    "^GSPC": ("SPX", "CBOE",    "USD"),
    "^DJI": ("INDU", "CME",     "USD"),
    "NKY":  ("N225", "OSE.JPN", "JPY"),
    "HSI":  ("HSI",  "HKFE",    "HKD"),
}


def _is_valid(val) -> bool:
    """Check if an IB ticker value is usable (not None, nan, 0, or -1)."""
    if val is None:
        return False
    try:
        if math.isnan(val):
            return False
    except (TypeError, ValueError):
        return False
    if val <= 0:
        return False
    return True


class IBKRProvider(MarketDataProvider):
    """Interactive Brokers provider using TWS/IB Gateway."""

    name = "ibkr"
    supported_markets: list[Market] = ["US", "JP", "HK"]
    _executor = ThreadPoolExecutor(max_workers=1)

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,  # 7497 = paper trading, 7496 = live
        client_id: int = 1,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.client_id = client_id
        self.timeout = timeout
        self._ib: IB | None = None

    def _ensure_connected(self) -> IB:
        """Connect synchronously (runs in executor thread)."""
        if self._ib is not None and self._ib.isConnected():
            return self._ib
        # Ensure an event loop exists in the worker thread
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
        self._ib = IB()
        self._ib.connect(
            self.host,
            self.port,
            clientId=self.client_id,
            timeout=self.timeout,
        )
        # Use delayed-frozen data as fallback when real-time is unavailable.
        # Type 1 = live, 2 = frozen, 3 = delayed, 4 = delayed-frozen.
        self._ib.reqMarketDataType(4)
        return self._ib

    async def disconnect(self):
        """Disconnect from TWS/IB Gateway."""
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            self._ib = None

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_timezone(self, market: Market) -> ZoneInfo:
        tzmap = {
            "US": ZoneInfo("America/New_York"),
            "JP": ZoneInfo("Asia/Tokyo"),
            "HK": ZoneInfo("Asia/Hong_Kong"),
        }
        return tzmap[market]

    def _get_exchange(self, market: Market) -> str:
        exchange_map = {
            "US": "SMART",
            "JP": "TSEJ",
            "HK": "SEHK",
        }
        return exchange_map[market]

    def _get_currency(self, market: Market) -> str:
        currency_map = {
            "US": "USD",
            "JP": "JPY",
            "HK": "HKD",
        }
        return currency_map[market]

    def _normalize_symbol(self, symbol: str, market: Market) -> str:
        """Normalize symbol for IB format."""
        if market == "JP" and symbol.endswith(".T"):
            return symbol[:-2]
        if market == "HK" and symbol.endswith(".HK"):
            return symbol[:-3]
        return symbol

    def _create_stock_contract(self, symbol: str, market: Market) -> Stock:
        clean_symbol = self._normalize_symbol(symbol, market)
        return Stock(
            symbol=clean_symbol,
            exchange=self._get_exchange(market),
            currency=self._get_currency(market),
        )

    def _create_contract(self, symbol: str, market: Market) -> Contract:
        """Create appropriate IB contract -- Index for known indices, Stock otherwise."""
        index_info = _INDEX_MAP.get(symbol)
        if index_info:
            ib_symbol, exchange, currency = index_info
            return Index(symbol=ib_symbol, exchange=exchange, currency=currency)
        return self._create_stock_contract(symbol, market)

    def _is_index(self, symbol: str) -> bool:
        return symbol in _INDEX_MAP

    def _extract_greeks(self, ticker) -> Greeks | None:
        if not ticker.modelGreeks:
            return None
        g = ticker.modelGreeks
        return Greeks(
            delta=float(g.delta) if _is_valid(g.delta) else 0.0,
            gamma=float(g.gamma) if _is_valid(g.gamma) else 0.0,
            theta=float(g.theta) if _is_valid(g.theta) else 0.0,
            vega=float(g.vega) if _is_valid(g.vega) else 0.0,
            rho=float(g.rho) if _is_valid(g.rho) else 0.0,
        )

    # ── Async public API (delegates to sync methods in executor) ─────

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Get real-time quote from IB (falls back to delayed/historical)."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_quote_sync, symbol, market
        )

    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Get option chain from IB."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_option_chain_sync, symbol, market, expiration
        )

    async def get_volatility_surface(
        self,
        symbol: str,
        market: Market,
    ) -> VolatilitySurface:
        """Build volatility surface from option chain data."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_volatility_surface_sync, symbol, market
        )

    async def get_price_history(
        self,
        symbol: str,
        market: Market,
        interval: str = "1d",
        limit: int = 30,
    ) -> PriceHistory:
        """Get historical price data from IB."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor, self._get_price_history_sync, symbol, market, interval, limit
        )

    # ── Sync implementations (run in dedicated thread) ───────────────

    def _historical_what_to_show(self, symbol: str) -> str:
        """Indices use TRADES for historical data; most work with this."""
        return "TRADES"

    def _get_quote_sync(self, symbol: str, market: Market) -> Quote:
        ib = self._ensure_connected()
        tz = self._get_timezone(market)

        contract = self._create_contract(symbol, market)
        try:
            ib.qualifyContracts(contract)
        except Exception:
            # Contract not found -- return empty quote
            return Quote(
                symbol=symbol, market=market, price=0.0,
                timestamp=datetime.now(tz),
            )

        # Request market data
        ib.reqMktData(contract, "", False, False)
        ticker = ib.ticker(contract)

        # Wait for any data with timeout (6s max)
        for _ in range(30):
            ib.sleep(0.2)
            if _is_valid(ticker.last) or _is_valid(ticker.bid) or _is_valid(ticker.close):
                ib.sleep(0.3)
                break

        ib.cancelMktData(contract)

        # Determine best price: last > close > bid
        price = 0.0
        if _is_valid(ticker.last):
            price = float(ticker.last)
        elif _is_valid(ticker.close):
            price = float(ticker.close)
        elif _is_valid(ticker.bid):
            price = float(ticker.bid)

        # Compute change from previous close
        change = None
        change_percent = None

        if _is_valid(ticker.close) and price > 0:
            prev_close = float(ticker.close)
            if price != prev_close:
                change = round(price - prev_close, 2)
                change_percent = round((change / prev_close) * 100, 2)

        # If no live change data or no price at all, fetch from recent history
        if change is None or price <= 0:
            try:
                bars = ib.reqHistoricalData(
                    contract,
                    endDateTime="",
                    durationStr="5 D",
                    barSizeSetting="1 day",
                    whatToShow=self._historical_what_to_show(symbol),
                    useRTH=True,
                )
                if len(bars) >= 2:
                    prev_close = float(bars[-2].close)
                    latest_close = float(bars[-1].close)
                    if price <= 0:
                        price = latest_close
                    change = round(latest_close - prev_close, 2)
                    change_percent = round((change / prev_close) * 100, 2) if prev_close else None
                elif len(bars) == 1:
                    if price <= 0:
                        price = float(bars[-1].close)
            except Exception:
                pass

        return Quote(
            symbol=symbol,
            market=market,
            price=price,
            change=change,
            change_percent=change_percent,
            bid=float(ticker.bid) if _is_valid(ticker.bid) else None,
            ask=float(ticker.ask) if _is_valid(ticker.ask) else None,
            volume=int(ticker.volume) if _is_valid(ticker.volume) else 0,
            timestamp=datetime.now(tz),
        )

    def _get_option_chain_sync(
        self, symbol: str, market: Market, expiration: str | None
    ) -> OptionChain:
        ib = self._ensure_connected()
        tz = self._get_timezone(market)

        stock = self._create_stock_contract(symbol, market)
        ib.qualifyContracts(stock)

        chains = ib.reqSecDefOptParams(
            stock.symbol, "", stock.secType, stock.conId
        )

        if not chains:
            return OptionChain(
                underlying=symbol,
                market=market,
                expirations=[],
                calls=[],
                puts=[],
                timestamp=datetime.now(tz),
            )

        chain = chains[0]
        available_expirations = sorted(chain.expirations)
        strikes = sorted(chain.strikes)

        if expiration:
            exp_str = expiration.replace("-", "")
            if exp_str in available_expirations:
                available_expirations = [exp_str]
            else:
                available_expirations = available_expirations[:1]

        # Limit to first 3 expirations to avoid too many requests
        available_expirations = available_expirations[:3]

        # Get underlying price for ATM filtering
        quote = self._get_quote_sync(symbol, market)
        underlying_price = quote.price if quote.price > 0 else 100.0

        # Filter strikes to +/- 10% of underlying
        atm_strikes = [
            s for s in strikes
            if underlying_price * 0.9 <= s <= underlying_price * 1.1
        ][:11]

        calls = []
        puts = []
        parsed_expirations = []

        for exp_str in available_expirations:
            exp_date = date(
                int(exp_str[:4]), int(exp_str[4:6]), int(exp_str[6:8])
            )
            parsed_expirations.append(exp_date)

            for strike in atm_strikes:
                for right in ["C", "P"]:
                    option = Option(
                        symbol=stock.symbol,
                        lastTradeDateOrContractMonth=exp_str,
                        strike=strike,
                        right=right,
                        exchange=chain.exchange,
                        currency=self._get_currency(market),
                    )
                    try:
                        ib.qualifyContracts(option)
                        ib.reqMktData(option, "", False, False)
                        ticker = ib.ticker(option)
                        ib.sleep(0.3)

                        iv = None
                        if ticker.modelGreeks and _is_valid(ticker.modelGreeks.impliedVol):
                            iv = float(ticker.modelGreeks.impliedVol)

                        contract_data = OptionContract(
                            symbol=option.localSymbol or f"{symbol}{exp_str}{right}{int(strike)}",
                            underlying=symbol,
                            strike=strike,
                            expiration=exp_date,
                            option_type="call" if right == "C" else "put",
                            bid=float(ticker.bid) if _is_valid(ticker.bid) else None,
                            ask=float(ticker.ask) if _is_valid(ticker.ask) else None,
                            last_price=float(ticker.last) if _is_valid(ticker.last) else None,
                            volume=int(ticker.volume) if _is_valid(ticker.volume) else 0,
                            open_interest=0,
                            implied_volatility=iv,
                            greeks=self._extract_greeks(ticker),
                        )

                        if right == "C":
                            calls.append(contract_data)
                        else:
                            puts.append(contract_data)

                        ib.cancelMktData(option)
                    except Exception:
                        continue

        return OptionChain(
            underlying=symbol,
            market=market,
            expirations=sorted(parsed_expirations),
            calls=calls,
            puts=puts,
            timestamp=datetime.now(tz),
        )

    def _get_volatility_surface_sync(self, symbol: str, market: Market) -> VolatilitySurface:
        chain = self._get_option_chain_sync(symbol, market, None)
        tz = self._get_timezone(market)

        if not chain.calls:
            return VolatilitySurface(
                symbol=symbol,
                market=market,
                strikes=[],
                expirations=[],
                call_ivs=[],
                put_ivs=[],
                timestamp=datetime.now(tz),
            )

        strikes = sorted(set(c.strike for c in chain.calls))
        expirations = sorted(chain.expirations)

        call_iv_map = {
            (c.expiration, c.strike): c.implied_volatility
            for c in chain.calls if c.implied_volatility
        }
        put_iv_map = {
            (p.expiration, p.strike): p.implied_volatility
            for p in chain.puts if p.implied_volatility
        }

        call_ivs = []
        put_ivs = []
        for exp in expirations:
            call_ivs.append([call_iv_map.get((exp, s), 0.0) for s in strikes])
            put_ivs.append([put_iv_map.get((exp, s), 0.0) for s in strikes])

        return VolatilitySurface(
            symbol=symbol,
            market=market,
            strikes=strikes,
            expirations=expirations,
            call_ivs=call_ivs,
            put_ivs=put_ivs,
            timestamp=datetime.now(tz),
        )

    def _get_price_history_sync(
        self, symbol: str, market: Market, interval: str, limit: int
    ) -> PriceHistory:
        ib = self._ensure_connected()
        tz = self._get_timezone(market)

        contract = self._create_contract(symbol, market)
        try:
            ib.qualifyContracts(contract)
        except Exception:
            return PriceHistory(
                symbol=symbol, market=market, interval=interval, bars=[]
            )

        bar_size_map = {"5m": "5 mins", "1h": "1 hour", "1d": "1 day"}
        bar_size = bar_size_map.get(interval, "1 day")

        duration_map = {"5m": "1 D", "1h": "1 W", "1d": "3 M"}
        duration = duration_map.get(interval, "3 M")

        try:
            bars_data = ib.reqHistoricalData(
                contract,
                endDateTime="",
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=self._historical_what_to_show(symbol),
                useRTH=True,
            )

            bars = []
            for bar in bars_data[-limit:]:
                ts = bar.date
                if isinstance(ts, date) and not isinstance(ts, datetime):
                    ts = datetime(ts.year, ts.month, ts.day, tzinfo=tz)
                elif ts.tzinfo is None:
                    ts = ts.replace(tzinfo=tz)

                bars.append(PriceBar(
                    timestamp=ts,
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=int(bar.volume),
                ))

            return PriceHistory(
                symbol=symbol, market=market, interval=interval, bars=bars
            )
        except Exception:
            return PriceHistory(
                symbol=symbol, market=market, interval=interval, bars=[]
            )
