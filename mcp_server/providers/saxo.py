"""SAXO OpenAPI data provider."""

import asyncio
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx

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


class SAXOProvider(MarketDataProvider):
    """SAXO Bank OpenAPI provider.

    Requires OAuth2 authentication. Get credentials from:
    https://www.developer.saxo/openapi/learn
    """

    name = "saxo"
    supported_markets: list[Market] = ["US", "JP", "HK"]

    # API endpoints
    SIM_BASE_URL = "https://gateway.saxobank.com/sim/openapi"
    LIVE_BASE_URL = "https://gateway.saxobank.com/openapi"

    def __init__(
        self,
        access_token: str,
        environment: str = "sim",  # "sim" or "live"
        timeout: float = 30.0,
    ):
        self.access_token = access_token
        self.base_url = self.SIM_BASE_URL if environment == "sim" else self.LIVE_BASE_URL
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_timezone(self, market: Market) -> ZoneInfo:
        tzmap = {
            "US": ZoneInfo("America/New_York"),
            "JP": ZoneInfo("Asia/Tokyo"),
            "HK": ZoneInfo("Asia/Hong_Kong"),
        }
        return tzmap[market]

    def _get_exchange_id(self, market: Market) -> str:
        """Get SAXO exchange ID for market."""
        # SAXO uses specific exchange IDs
        exchange_map = {
            "US": "NYSE",  # Also NASDAQ, AMEX
            "JP": "TSE",
            "HK": "HKEX",
        }
        return exchange_map[market]

    def _get_asset_type(self, market: Market) -> str:
        """Get SAXO asset type."""
        return "Stock"

    async def _search_instrument(
        self, symbol: str, market: Market
    ) -> dict | None:
        """Search for instrument to get Uic (unique identifier)."""
        client = await self._get_client()

        # Clean symbol
        clean_symbol = symbol.replace(".T", "").replace(".HK", "")

        params = {
            "Keywords": clean_symbol,
            "AssetTypes": "Stock,StockOption",
            "ExchangeId": self._get_exchange_id(market),
        }

        try:
            response = await client.get("/ref/v1/instruments", params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("Data"):
                # Find exact match
                for instrument in data["Data"]:
                    if instrument.get("Symbol", "").upper() == clean_symbol.upper():
                        return instrument
                # Return first result if no exact match
                return data["Data"][0]
        except httpx.HTTPError:
            pass

        return None

    async def _get_info_price(self, uic: int, asset_type: str) -> dict | None:
        """Get info price for an instrument."""
        client = await self._get_client()

        params = {
            "Uic": uic,
            "AssetType": asset_type,
            "FieldGroups": "DisplayAndFormat,InstrumentPriceDetails,PriceInfo,Quote",
        }

        try:
            response = await client.get("/trade/v1/infoprices", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    async def get_quote(self, symbol: str, market: Market) -> Quote:
        """Get real-time quote from SAXO."""
        instrument = await self._search_instrument(symbol, market)

        if not instrument:
            return Quote(
                symbol=symbol,
                market=market,
                price=0.0,
                bid=None,
                ask=None,
                volume=0,
                timestamp=datetime.now(self._get_timezone(market)),
            )

        uic = instrument.get("Identifier")
        asset_type = instrument.get("AssetType", "Stock")

        price_data = await self._get_info_price(uic, asset_type)

        if not price_data:
            return Quote(
                symbol=symbol,
                market=market,
                price=0.0,
                timestamp=datetime.now(self._get_timezone(market)),
            )

        quote_info = price_data.get("Quote", {})
        price_info = price_data.get("PriceInfo", {})

        return Quote(
            symbol=symbol,
            market=market,
            price=float(quote_info.get("Mid") or quote_info.get("Ask") or 0),
            bid=float(quote_info.get("Bid")) if quote_info.get("Bid") else None,
            ask=float(quote_info.get("Ask")) if quote_info.get("Ask") else None,
            volume=int(price_info.get("Volume", 0)),
            timestamp=datetime.now(self._get_timezone(market)),
        )

    async def _get_option_chain_data(
        self, underlying_uic: int, expiration: str | None = None
    ) -> list[dict]:
        """Get option chain from SAXO."""
        client = await self._get_client()

        params = {
            "OptionRootId": underlying_uic,
            "FieldGroups": "DisplayAndFormat,Greeks,PriceInfo",
        }

        try:
            response = await client.get(
                "/ref/v1/instruments/contractoptionspaces", params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get("Data", [])
        except httpx.HTTPError:
            return []

    async def get_option_chain(
        self,
        symbol: str,
        market: Market,
        expiration: str | None = None,
    ) -> OptionChain:
        """Get option chain from SAXO."""
        instrument = await self._search_instrument(symbol, market)

        if not instrument:
            return OptionChain(
                underlying=symbol,
                market=market,
                expirations=[],
                calls=[],
                puts=[],
                timestamp=datetime.now(self._get_timezone(market)),
            )

        underlying_uic = instrument.get("Identifier")

        # Get underlying price
        quote = await self.get_quote(symbol, market)
        underlying_price = quote.price if quote.price > 0 else 100.0

        # Get option contracts
        client = await self._get_client()

        calls = []
        puts = []
        expirations_set = set()

        try:
            # Search for stock options on this underlying
            params = {
                "Keywords": symbol.replace(".T", "").replace(".HK", ""),
                "AssetTypes": "StockOption",
                "ExchangeId": self._get_exchange_id(market),
            }

            response = await client.get("/ref/v1/instruments", params=params)
            response.raise_for_status()
            data = response.json()

            for opt in data.get("Data", []):
                if opt.get("AssetType") != "StockOption":
                    continue

                # Parse option details from description or symbol
                opt_symbol = opt.get("Symbol", "")
                description = opt.get("Description", "")

                # Try to get option details
                opt_uic = opt.get("Identifier")
                price_data = await self._get_info_price(opt_uic, "StockOption")

                if not price_data:
                    continue

                # Extract expiry from instrument details
                display_format = price_data.get("DisplayAndFormat", {})
                expiry_str = display_format.get("ExpiryDate", "")

                if expiry_str:
                    try:
                        exp_date = date.fromisoformat(expiry_str[:10])
                        expirations_set.add(exp_date)
                    except ValueError:
                        continue
                else:
                    continue

                # Filter by expiration if specified
                if expiration and str(exp_date) != expiration:
                    continue

                quote_info = price_data.get("Quote", {})
                greeks_info = price_data.get("Greeks", {})

                strike = float(display_format.get("Strike", 0))
                is_call = "Call" in description or "C" in opt_symbol.upper()

                contract = OptionContract(
                    symbol=opt_symbol,
                    underlying=symbol,
                    strike=strike,
                    expiration=exp_date,
                    option_type="call" if is_call else "put",
                    bid=float(quote_info.get("Bid")) if quote_info.get("Bid") else None,
                    ask=float(quote_info.get("Ask")) if quote_info.get("Ask") else None,
                    last_price=float(quote_info.get("Mid")) if quote_info.get("Mid") else None,
                    volume=0,
                    open_interest=0,
                    implied_volatility=float(greeks_info.get("ImpliedVolatility")) if greeks_info.get("ImpliedVolatility") else None,
                    greeks=Greeks(
                        delta=float(greeks_info.get("Delta", 0)),
                        gamma=float(greeks_info.get("Gamma", 0)),
                        theta=float(greeks_info.get("Theta", 0)),
                        vega=float(greeks_info.get("Vega", 0)),
                        rho=float(greeks_info.get("Rho", 0)),
                    ) if greeks_info else None,
                )

                if is_call:
                    calls.append(contract)
                else:
                    puts.append(contract)

        except httpx.HTTPError:
            pass

        return OptionChain(
            underlying=symbol,
            market=market,
            expirations=sorted(expirations_set),
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
        strikes = sorted(set(c.strike for c in chain.calls if c.strike > 0))
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
        """Get historical price data from SAXO."""
        instrument = await self._search_instrument(symbol, market)

        if not instrument:
            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=[],
            )

        uic = instrument.get("Identifier")
        asset_type = instrument.get("AssetType", "Stock")

        client = await self._get_client()

        # Map interval to SAXO horizon
        horizon_map = {
            "5m": 60,      # 1 hour of 5m bars
            "1h": 1440,    # 1 day of 1h bars
            "1d": 10080,   # 1 week of daily bars
        }
        horizon = horizon_map.get(interval, 10080)

        try:
            params = {
                "Uic": uic,
                "AssetType": asset_type,
                "Horizon": horizon,
                "Count": limit,
            }

            response = await client.get("/chart/v1/charts", params=params)
            response.raise_for_status()
            data = response.json()

            bars = []
            for bar_data in data.get("Data", []):
                bars.append(PriceBar(
                    timestamp=datetime.fromisoformat(bar_data["Time"].replace("Z", "+00:00")),
                    open=float(bar_data.get("Open", 0)),
                    high=float(bar_data.get("High", 0)),
                    low=float(bar_data.get("Low", 0)),
                    close=float(bar_data.get("Close", 0)),
                    volume=int(bar_data.get("Volume", 0)),
                ))

            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=bars,
            )
        except httpx.HTTPError:
            return PriceHistory(
                symbol=symbol,
                market=market,
                interval=interval,
                bars=[],
            )
