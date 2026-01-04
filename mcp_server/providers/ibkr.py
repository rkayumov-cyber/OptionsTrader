"""Interactive Brokers data provider using ib_insync."""

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

from ib_insync import IB, Contract, Option, Stock, util

from mcp_server.models import (
    Greeks,
    Market,
    OptionChain,
    OptionContract,
    Quote,
    VolatilitySurface,
)
from mcp_server.providers.base import MarketDataProvider


class IBKRProvider(MarketDataProvider):
    """Interactive Brokers provider using TWS/IB Gateway."""

    name = "ibkr"
    supported_markets: list[Market] = ["US", "JP", "HK"]

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

    async def _connect(self) -> IB:
        """Connect to TWS/IB Gateway if not already connected."""
        if self._ib is None or not self._ib.isConnected():
            self._ib = IB()
            await self._ib.connectAsync(
                self.host,
                self.port,
                clientId=self.client_id,
                timeout=self.timeout,
            )
        return self._ib

    async def disconnect(self):
        """Disconnect from TWS/IB Gateway."""
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            self._ib = None

    def _get_timezone(self, market: Market) -> ZoneInfo:
        tzmap = {
            "US": ZoneInfo("America/New_York"),
            "JP": ZoneInfo("Asia/Tokyo"),
            "HK": ZoneInfo("Asia/Hong_Kong"),
        }
        return tzmap[market]

    def _get_exchange(self, market: Market) -> str:
        """Get primary exchange for market."""
        exchange_map = {
            "US": "SMART",
            "JP": "TSEJ",
            "HK": "SEHK",
        }
        return exchange_map[market]

    def _get_currency(self, market: Market) -> str:
        """Get currency for market."""
        currency_map = {
            "US": "USD",
            "JP": "JPY",
            "HK": "HKD",
        }
        return currency_map[market]

    def _normalize_symbol(self, symbol: str, market: Market) -> str:
        """Normalize symbol for IB format."""
        # Remove market suffixes if present
        if market == "JP" and symbol.endswith(".T"):
            return symbol[:-2]
        if market == "HK" and symbol.endswith(".HK"):
            return symbol[:-3]
        return symbol

    def _create_stock_contract(self, symbol: str, market: Market) -> Stock:
        """Create IB Stock contract."""
        clean_symbol = self._normalize_symbol(symbol, market)
        return Stock(
            symbol=clean_symbol,
            exchange=self._get_exchange(market),
            currency=self._get_currency(market),
        )

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Get real-time quote from IB."""
        ib = await self._connect()

        contract = self._create_stock_contract(symbol, market)
        await ib.qualifyContractsAsync(contract)

        # Request market data
        ib.reqMktData(contract, "", False, False)
        ticker = ib.ticker(contract)

        # Wait for data with timeout
        timeout = 5.0
        elapsed = 0.0
        while elapsed < timeout:
            await asyncio.sleep(0.1)
            elapsed += 0.1
            if ticker.last is not None or ticker.bid is not None:
                break

        # Cancel market data subscription
        ib.cancelMktData(contract)

        price = ticker.last if ticker.last and ticker.last > 0 else ticker.close
        if price is None or price <= 0:
            price = ticker.bid if ticker.bid else 0.0

        return Quote(
            symbol=symbol,
            market=market,
            price=float(price) if price else 0.0,
            bid=float(ticker.bid) if ticker.bid else None,
            ask=float(ticker.ask) if ticker.ask else None,
            volume=int(ticker.volume) if ticker.volume else 0,
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Get option chain from IB."""
        ib = await self._connect()

        # Get underlying contract
        stock = self._create_stock_contract(symbol, market)
        await ib.qualifyContractsAsync(stock)

        # Get option chain parameters
        chains = await ib.reqSecDefOptParamsAsync(
            stock.symbol,
            "",
            stock.secType,
            stock.conId,
        )

        if not chains:
            return OptionChain(
                underlying=symbol,
                market=market,
                expirations=[],
                calls=[],
                puts=[],
                timestamp=datetime.now(self._get_timezone(market)),
            )

        # Use first chain (usually SMART exchange)
        chain = chains[0]
        available_expirations = sorted(chain.expirations)
        strikes = sorted(chain.strikes)

        # Filter expirations if specified
        if expiration:
            exp_str = expiration.replace("-", "")
            if exp_str in available_expirations:
                available_expirations = [exp_str]
            else:
                available_expirations = available_expirations[:1]

        # Limit to first 3 expirations and strikes around ATM to avoid too many requests
        available_expirations = available_expirations[:3]

        # Get underlying price for ATM filtering
        quote = await self.get_quote(symbol, market)
        underlying_price = quote.price if quote.price > 0 else 100.0

        # Filter strikes to +/- 10% of underlying
        atm_strikes = [
            s for s in strikes
            if underlying_price * 0.9 <= s <= underlying_price * 1.1
        ][:11]  # Max 11 strikes

        calls = []
        puts = []
        parsed_expirations = []

        for exp_str in available_expirations:
            # Parse expiration (YYYYMMDD format)
            exp_date = date(
                int(exp_str[:4]),
                int(exp_str[4:6]),
                int(exp_str[6:8]),
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
                        await ib.qualifyContractsAsync(option)
                        ib.reqMktData(option, "", False, False)
                        ticker = ib.ticker(option)

                        # Brief wait for data
                        await asyncio.sleep(0.2)

                        contract_data = OptionContract(
                            symbol=option.localSymbol or f"{symbol}{exp_str}{right}{int(strike)}",
                            underlying=symbol,
                            strike=strike,
                            expiration=exp_date,
                            option_type="call" if right == "C" else "put",
                            bid=float(ticker.bid) if ticker.bid else None,
                            ask=float(ticker.ask) if ticker.ask else None,
                            last_price=float(ticker.last) if ticker.last else None,
                            volume=int(ticker.volume) if ticker.volume else 0,
                            open_interest=0,  # Requires separate request
                            implied_volatility=float(ticker.modelGreeks.impliedVol) if ticker.modelGreeks and ticker.modelGreeks.impliedVol else None,
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
            timestamp=datetime.now(self._get_timezone(market)),
        )

    def _extract_greeks(self, ticker) -> Greeks | None:
        """Extract Greeks from ticker if available."""
        if not ticker.modelGreeks:
            return None

        g = ticker.modelGreeks
        return Greeks(
            delta=float(g.delta) if g.delta else 0.0,
            gamma=float(g.gamma) if g.gamma else 0.0,
            theta=float(g.theta) if g.theta else 0.0,
            vega=float(g.vega) if g.vega else 0.0,
            rho=float(g.rho) if g.rho else 0.0,
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
