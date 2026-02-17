"""FastAPI REST API for Options Trader."""

from datetime import datetime, date
from typing import Literal
import math

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mcp_server.models import (
    Market,
    PayoffLeg,
    PositionLeg,
    ScanCriteria,
    AlertRuleType,
    BondRatesData,
    CommoditiesData,
    SectorData,
    MarketBreadthData,
    MarketIndicatorsResponse,
)
from mcp_server.providers import MockProvider, YahooProvider, IBKRProvider, SAXOProvider
from mcp_server.providers.base import MarketDataProvider
from mcp_server.services.payoff import payoff_calculator
from mcp_server.services.positions import position_service
from mcp_server.services.scanner import scanner_service
from mcp_server.services.paper_trading import paper_trading_service
from mcp_server.services.journal import journal_service
from mcp_server.services.alerts import alert_service
from mcp_server.services.jpm_research import jpm_research_service
from mcp_server.models import JPMStrategyType, JPMScreenType


app = FastAPI(
    title="Options Trader API",
    description="REST API for cross-market equities options data",
    version="0.1.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Provider registry
providers: dict[str, MarketDataProvider] = {
    "mock": MockProvider(),
    "yahoo": YahooProvider(),
}
active_provider_name: str = "mock"

# In-memory watchlist — seeded with most liquid options names
_DEFAULT_WATCHLIST = [
    # ETFs
    ("SPY",  "US", "SPDR S&P 500 ETF"),
    ("QQQ",  "US", "Invesco QQQ Trust"),
    ("IWM",  "US", "iShares Russell 2000 ETF"),
    # Mega-cap tech
    ("AAPL", "US", "Apple Inc."),
    ("MSFT", "US", "Microsoft Corporation"),
    ("NVDA", "US", "NVIDIA Corporation"),
    ("AMZN", "US", "Amazon.com Inc."),
    ("META", "US", "Meta Platforms Inc."),
    ("GOOGL","US", "Alphabet Inc."),
    ("TSLA", "US", "Tesla Inc."),
    # High options volume
    ("AMD",  "US", "Advanced Micro Devices"),
    ("NFLX", "US", "Netflix Inc."),
    ("COIN", "US", "Coinbase Global Inc."),
    ("SOFI", "US", "SoFi Technologies Inc."),
    ("PLTR", "US", "Palantir Technologies"),
    ("BAC",  "US", "Bank of America Corp."),
    ("JPM",  "US", "JPMorgan Chase & Co."),
    ("XOM",  "US", "Exxon Mobil Corporation"),
    # Asia
    ("7203.T","JP", "Toyota Motor Corp"),
    ("0700.HK","HK","Tencent Holdings"),
]

watchlist: list[dict] = [
    {
        "symbol": sym,
        "market": mkt,
        "name": name,
        "added_at": datetime.now().isoformat(),
    }
    for sym, mkt, name in _DEFAULT_WATCHLIST
]


def get_provider() -> MarketDataProvider:
    """Get active provider."""
    return providers[active_provider_name]


# Request/Response models
class WatchlistItem(BaseModel):
    symbol: str
    market: Market
    name: str | None = None


class SwitchProviderRequest(BaseModel):
    provider: str
    host: str | None = None
    port: int | None = None
    client_id: int | None = None
    access_token: str | None = None
    environment: str | None = None


# =============================================================================
# QUOTE ENDPOINTS
# =============================================================================


@app.get("/api/quote/{symbol}")
async def get_quote(symbol: str, market: Market = Query(default="US")):
    """Get real-time quote for a symbol."""
    try:
        provider = get_provider()
        quote = await provider.get_quote(symbol, market)
        return quote.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# OPTIONS ENDPOINTS
# =============================================================================


@app.get("/api/options/{symbol}")
async def get_options(
    symbol: str,
    market: Market = Query(default="US"),
    expiration: str | None = Query(default=None),
):
    """Get option chain for a symbol."""
    try:
        provider = get_provider()
        chain = await provider.get_option_chain(symbol, market, expiration)
        return {
            "underlying": chain.underlying,
            "market": chain.market,
            "expirations": [str(e) for e in chain.expirations],
            "calls": [c.model_dump() for c in chain.calls],
            "puts": [p.model_dump() for p in chain.puts],
            "timestamp": chain.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# VOLATILITY ENDPOINTS
# =============================================================================


@app.get("/api/volatility/{symbol}")
async def get_volatility(symbol: str, market: Market = Query(default="US")):
    """Get volatility surface for a symbol."""
    try:
        provider = get_provider()
        surface = await provider.get_volatility_surface(symbol, market)
        return {
            "symbol": surface.symbol,
            "market": surface.market,
            "strikes": surface.strikes,
            "expirations": [str(e) for e in surface.expirations],
            "call_ivs": surface.call_ivs,
            "put_ivs": surface.put_ivs,
            "timestamp": surface.timestamp.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HISTORY ENDPOINTS
# =============================================================================


@app.get("/api/history/{symbol}")
async def get_history(
    symbol: str,
    market: Market = Query(default="US"),
    interval: str = Query(default="1d"),
    limit: int = Query(default=30),
):
    """Get historical price data for a symbol."""
    try:
        provider = get_provider()
        history = await provider.get_price_history(symbol, market, interval, limit)
        return {
            "symbol": history.symbol,
            "market": history.market,
            "interval": history.interval,
            "bars": [
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                }
                for bar in history.bars
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WATCHLIST ENDPOINTS
# =============================================================================


@app.get("/api/watchlist")
async def get_watchlist():
    """Get current watchlist."""
    return watchlist


@app.post("/api/watchlist")
async def add_to_watchlist(item: WatchlistItem):
    """Add symbol to watchlist."""
    # Check if already exists
    for w in watchlist:
        if w["symbol"] == item.symbol and w["market"] == item.market:
            return {"message": f"{item.symbol} already in watchlist"}

    watchlist.append({
        "symbol": item.symbol,
        "market": item.market,
        "name": item.name,
        "added_at": datetime.now().isoformat(),
    })
    return {"message": f"Added {item.symbol} to watchlist"}


@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, market: Market = Query(default="US")):
    """Remove symbol from watchlist."""
    global watchlist
    original_len = len(watchlist)
    watchlist = [w for w in watchlist if not (w["symbol"] == symbol and w["market"] == market)]

    if len(watchlist) < original_len:
        return {"message": f"Removed {symbol} from watchlist"}
    raise HTTPException(status_code=404, detail=f"{symbol} not found in watchlist")


# =============================================================================
# PROVIDER ENDPOINTS
# =============================================================================


@app.get("/api/providers")
async def list_providers():
    """List available providers."""
    return {
        "active": active_provider_name,
        "available": [
            {
                "name": name,
                "markets": p.supported_markets,
                "active": name == active_provider_name,
            }
            for name, p in providers.items()
        ],
    }


@app.post("/api/providers/switch")
async def switch_provider(request: SwitchProviderRequest):
    """Switch to a different provider."""
    global active_provider_name

    name = request.provider.lower()

    if name in providers:
        active_provider_name = name
        return {"message": f"Switched to {name} provider"}

    if name == "ibkr":
        try:
            ibkr = IBKRProvider(
                host=request.host or "127.0.0.1",
                port=request.port or 7497,
                client_id=request.client_id or 1,
            )
            providers["ibkr"] = ibkr
            active_provider_name = "ibkr"
            return {"message": "Switched to IBKR provider"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize IBKR: {e}")

    if name == "saxo":
        if not request.access_token:
            raise HTTPException(status_code=400, detail="SAXO requires access_token")
        try:
            saxo = SAXOProvider(
                access_token=request.access_token,
                environment=request.environment or "sim",
            )
            providers["saxo"] = saxo
            active_provider_name = "saxo"
            return {"message": f"Switched to SAXO provider ({request.environment or 'sim'})"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize SAXO: {e}")

    raise HTTPException(status_code=400, detail=f"Unknown provider: {name}")


# =============================================================================
# MARKETS ENDPOINT
# =============================================================================


@app.get("/api/markets")
async def get_markets():
    """Get supported markets info."""
    return {
        "US": {
            "code": "US",
            "name": "United States",
            "currency": "USD",
            "timezone": "America/New_York",
            "trading_hours": "09:30-16:00 ET",
        },
        "JP": {
            "code": "JP",
            "name": "Japan",
            "currency": "JPY",
            "timezone": "Asia/Tokyo",
            "trading_hours": "09:00-15:00 JST",
        },
        "HK": {
            "code": "HK",
            "name": "Hong Kong",
            "currency": "HKD",
            "timezone": "Asia/Hong_Kong",
            "trading_hours": "09:30-16:00 HKT",
        },
    }


# =============================================================================
# DASHBOARD ENDPOINTS
# =============================================================================


@app.get("/api/iv-analysis/{symbol}")
async def get_iv_analysis(symbol: str, market: Market = Query(default="US")):
    """Get IV rank and percentile analysis for a symbol."""
    try:
        provider = get_provider()
        analysis = await provider.get_iv_analysis(symbol, market)
        return analysis.model_dump()
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="IV analysis not supported by current provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/market-sentiment/{symbol}")
async def get_market_sentiment(symbol: str, market: Market = Query(default="US")):
    """Get put/call ratio and sentiment for a symbol."""
    try:
        provider = get_provider()
        sentiment = await provider.get_market_sentiment(symbol, market)
        return sentiment.model_dump()
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Market sentiment not supported by current provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/unusual-activity")
async def get_unusual_activity(market: Market | None = Query(default=None)):
    """Get unusual options activity alerts."""
    try:
        provider = get_provider()
        activity = await provider.get_unusual_activity(market)
        return {
            "alerts": [alert.model_dump() for alert in activity.alerts]
        }
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Unusual activity not supported by current provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/strategy-suggestions/{symbol}")
async def get_strategy_suggestions(symbol: str, market: Market = Query(default="US")):
    """Get strategy suggestions based on market conditions."""
    try:
        provider = get_provider()
        suggestions = await provider.get_strategy_suggestions(symbol, market)
        return suggestions.model_dump()
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Strategy suggestions not supported by current provider")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH CHECK
# =============================================================================


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "provider": active_provider_name,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# PAYOFF DIAGRAM ENDPOINTS
# =============================================================================


class PayoffRequest(BaseModel):
    legs: list[PayoffLeg]
    underlying_price: float
    price_range_percent: float = 30
    num_points: int = 100


@app.post("/api/payoff/calculate")
async def calculate_payoff(request: PayoffRequest):
    """Calculate payoff diagram for option legs."""
    try:
        result = payoff_calculator.calculate_payoff(
            legs=request.legs,
            underlying_price=request.underlying_price,
            price_range_percent=request.price_range_percent,
            num_points=request.num_points,
        )
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TimeSeriesPayoffRequest(BaseModel):
    """Request for time-series payoff calculation."""
    legs: list[PayoffLeg]
    underlying_price: float
    max_dte: int = 30
    iv: float = 0.30
    rate: float = 0.05
    price_range_percent: float = 30
    num_points: int = 50
    time_intervals: list[int] | None = None


@app.post("/api/payoff/time-series")
async def calculate_time_series_payoff(request: TimeSeriesPayoffRequest):
    """Calculate payoff curves at multiple time points (theta decay visualization)."""
    try:
        result = payoff_calculator.calculate_time_series_payoff(
            legs=request.legs,
            underlying_price=request.underlying_price,
            max_dte=request.max_dte,
            iv=request.iv,
            rate=request.rate,
            price_range_percent=request.price_range_percent,
            num_points=request.num_points,
            time_intervals=request.time_intervals,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/payoff/templates/{strategy}")
async def get_strategy_template(strategy: str, underlying_price: float = Query(default=100)):
    """Get predefined strategy leg templates."""
    legs = payoff_calculator.get_strategy_template(strategy, underlying_price)
    if not legs:
        raise HTTPException(status_code=404, detail=f"Unknown strategy: {strategy}")
    return {"strategy": strategy, "legs": [leg.model_dump() for leg in legs]}


@app.get("/api/payoff/strategies")
async def list_strategies():
    """List available strategy templates."""
    return {
        "strategies": [
            {"id": "long_call", "name": "Long Call", "legs": 1, "type": "bullish"},
            {"id": "long_put", "name": "Long Put", "legs": 1, "type": "bearish"},
            {"id": "covered_call", "name": "Covered Call", "legs": 1, "type": "neutral"},
            {"id": "bull_call_spread", "name": "Bull Call Spread", "legs": 2, "type": "bullish"},
            {"id": "bear_put_spread", "name": "Bear Put Spread", "legs": 2, "type": "bearish"},
            {"id": "long_straddle", "name": "Long Straddle", "legs": 2, "type": "volatile"},
            {"id": "short_straddle", "name": "Short Straddle", "legs": 2, "type": "neutral"},
            {"id": "long_strangle", "name": "Long Strangle", "legs": 2, "type": "volatile"},
            {"id": "iron_condor", "name": "Iron Condor", "legs": 4, "type": "neutral"},
            {"id": "iron_butterfly", "name": "Iron Butterfly", "legs": 4, "type": "neutral"},
        ]
    }


# =============================================================================
# POSITION TRACKING ENDPOINTS
# =============================================================================


class CreatePositionRequest(BaseModel):
    symbol: str
    market: Market = "US"
    strategy_name: str = "Custom"
    legs: list[PositionLeg]
    notes: str = ""


class UpdatePositionRequest(BaseModel):
    notes: str | None = None
    current_value: float | None = None
    status: str | None = None


@app.get("/api/positions")
async def get_positions():
    """Get all positions."""
    positions = position_service.get_all()
    return {"positions": [p.model_dump() for p in positions]}


@app.get("/api/positions/open")
async def get_open_positions():
    """Get open positions only."""
    positions = position_service.get_open()
    return {"positions": [p.model_dump() for p in positions]}


@app.get("/api/positions/summary")
async def get_portfolio_summary():
    """Get portfolio summary with aggregated Greeks."""
    summary = position_service.get_summary()
    return summary.model_dump()


@app.get("/api/positions/{position_id}")
async def get_position(position_id: str):
    """Get position by ID."""
    position = position_service.get_by_id(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position.model_dump()


@app.post("/api/positions")
async def create_position(request: CreatePositionRequest):
    """Create a new position."""
    position = position_service.create(
        symbol=request.symbol,
        market=request.market,
        legs=request.legs,
        strategy_name=request.strategy_name,
        notes=request.notes,
    )
    return position.model_dump()


@app.put("/api/positions/{position_id}")
async def update_position(position_id: str, request: UpdatePositionRequest):
    """Update a position."""
    updates = request.model_dump(exclude_none=True)
    position = position_service.update(position_id, updates)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position.model_dump()


@app.post("/api/positions/{position_id}/close")
async def close_position(position_id: str, exit_value: float | None = None):
    """Close a position."""
    position = position_service.close(position_id, exit_value)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position.model_dump()


@app.delete("/api/positions/{position_id}")
async def delete_position(position_id: str):
    """Delete a position."""
    if position_service.delete(position_id):
        return {"message": "Position deleted"}
    raise HTTPException(status_code=404, detail="Position not found")


# =============================================================================
# OPTIONS SCANNER ENDPOINTS
# =============================================================================


@app.post("/api/scanner/scan")
async def scan_options(criteria: ScanCriteria):
    """Scan for options matching criteria."""
    try:
        result = scanner_service.scan(criteria)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scanner/high-iv")
async def get_high_iv_opportunities(market: Market = Query(default="US")):
    """Find high IV rank opportunities."""
    result = scanner_service.get_high_iv_opportunities(market)
    return result.model_dump()


@app.get("/api/scanner/low-iv")
async def get_low_iv_opportunities(market: Market = Query(default="US")):
    """Find low IV rank opportunities."""
    result = scanner_service.get_low_iv_opportunities(market)
    return result.model_dump()


@app.get("/api/scanner/high-volume")
async def get_high_volume_activity(market: Market = Query(default="US")):
    """Find high volume activity."""
    result = scanner_service.get_high_volume_activity(market)
    return result.model_dump()


# =============================================================================
# PAPER TRADING ENDPOINTS
# =============================================================================


class CreateAccountRequest(BaseModel):
    name: str = "Default"
    initial_cash: float = 100000.0


class PlaceOrderRequest(BaseModel):
    symbol: str
    market: Market = "US"
    side: str  # "buy" or "sell"
    quantity: int
    order_type: str = "market"
    limit_price: float | None = None
    option_symbol: str | None = None


@app.get("/api/paper/accounts")
async def get_paper_accounts():
    """Get all paper trading accounts."""
    accounts = paper_trading_service.get_all_accounts()
    return {"accounts": [a.model_dump() for a in accounts]}


@app.post("/api/paper/accounts")
async def create_paper_account(request: CreateAccountRequest):
    """Create a new paper trading account."""
    account = paper_trading_service.create_account(request.name, request.initial_cash)
    return account.model_dump()


@app.get("/api/paper/accounts/default")
async def get_default_paper_account():
    """Get or create the default paper trading account."""
    # Try to find existing default account
    accounts = paper_trading_service.get_all_accounts()
    default_account = next((a for a in accounts if a.name == "Default"), None)

    if not default_account:
        # Create default account if it doesn't exist
        default_account = paper_trading_service.create_account("Default", 100000.0)

    return default_account.model_dump()


@app.get("/api/paper/accounts/{account_id}")
async def get_paper_account(account_id: str):
    """Get paper trading account by ID."""
    account = paper_trading_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.model_dump()


@app.post("/api/paper/accounts/{account_id}/reset")
async def reset_paper_account(account_id: str):
    """Reset paper trading account."""
    account = paper_trading_service.reset_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account.model_dump()


@app.post("/api/paper/orders")
async def place_paper_order(account_id: str, request: PlaceOrderRequest):
    """Place a paper trading order."""
    order = paper_trading_service.place_order(
        account_id=account_id,
        symbol=request.symbol,
        market=request.market,
        side=request.side,
        quantity=request.quantity,
        order_type=request.order_type,
        limit_price=request.limit_price,
        option_symbol=request.option_symbol,
    )
    if not order:
        raise HTTPException(status_code=404, detail="Account not found")
    return order.model_dump()


@app.get("/api/paper/positions")
async def get_paper_positions(account_id: str):
    """Get paper trading positions."""
    positions = paper_trading_service.get_positions(account_id)
    return {"positions": [p.model_dump() for p in positions]}


@app.get("/api/paper/orders")
async def get_paper_orders(account_id: str):
    """Get paper trading orders."""
    orders = paper_trading_service.get_orders(account_id)
    return {"orders": [o.model_dump() for o in orders]}


@app.delete("/api/paper/orders/{order_id}")
async def cancel_paper_order(account_id: str, order_id: str):
    """Cancel a paper trading order."""
    if paper_trading_service.cancel_order(account_id, order_id):
        return {"message": "Order cancelled"}
    raise HTTPException(status_code=404, detail="Order not found or not pending")


# =============================================================================
# TRADE JOURNAL ENDPOINTS
# =============================================================================


class CreateTradeRequest(BaseModel):
    symbol: str
    market: Market = "US"
    entry_price: float
    quantity: int
    strategy: str = "Custom"
    notes: str = ""
    tags: list[str] = []


class CloseTradeRequest(BaseModel):
    exit_price: float
    notes: str = ""
    lessons: str = ""


class UpdateTradeRequest(BaseModel):
    notes: str | None = None
    tags: list[str] | None = None
    lessons: str | None = None
    strategy: str | None = None


@app.get("/api/journal/trades")
async def get_trades():
    """Get all trades."""
    trades = journal_service.get_all()
    return {"trades": [t.model_dump() for t in trades]}


@app.get("/api/journal/trades/open")
async def get_open_trades():
    """Get open trades."""
    trades = journal_service.get_open_trades()
    return {"trades": [t.model_dump() for t in trades]}


@app.get("/api/journal/stats")
async def get_trade_stats():
    """Get trading statistics."""
    stats = journal_service.get_stats()
    return stats.model_dump()


@app.get("/api/journal/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get trade by ID."""
    trade = journal_service.get_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.model_dump()


@app.post("/api/journal/trades")
async def create_trade(request: CreateTradeRequest):
    """Create a new trade entry."""
    trade = journal_service.create(
        symbol=request.symbol,
        market=request.market,
        entry_price=request.entry_price,
        quantity=request.quantity,
        strategy=request.strategy,
        notes=request.notes,
        tags=request.tags,
    )
    return trade.model_dump()


@app.post("/api/journal/trades/{trade_id}/close")
async def close_trade(trade_id: str, request: CloseTradeRequest):
    """Close a trade."""
    trade = journal_service.close_trade(
        trade_id=trade_id,
        exit_price=request.exit_price,
        notes=request.notes,
        lessons=request.lessons,
    )
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.model_dump()


@app.put("/api/journal/trades/{trade_id}")
async def update_trade(trade_id: str, request: UpdateTradeRequest):
    """Update trade details."""
    updates = request.model_dump(exclude_none=True)
    trade = journal_service.update(trade_id, updates)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.model_dump()


@app.delete("/api/journal/trades/{trade_id}")
async def delete_trade(trade_id: str):
    """Delete a trade entry."""
    if journal_service.delete(trade_id):
        return {"message": "Trade deleted"}
    raise HTTPException(status_code=404, detail="Trade not found")


# =============================================================================
# ALERT SYSTEM ENDPOINTS
# =============================================================================


class CreateAlertRequest(BaseModel):
    symbol: str
    market: Market = "US"
    rule_type: AlertRuleType
    threshold: float


class UpdateAlertRequest(BaseModel):
    enabled: bool | None = None
    threshold: float | None = None


@app.get("/api/alerts/rules")
async def get_alert_rules():
    """Get all alert rules."""
    rules = alert_service.get_all_rules()
    return {"rules": [r.model_dump() for r in rules]}


@app.get("/api/alerts/rules/{rule_id}")
async def get_alert_rule(rule_id: str):
    """Get alert rule by ID."""
    rule = alert_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


@app.post("/api/alerts/rules")
async def create_alert_rule(request: CreateAlertRequest):
    """Create a new alert rule."""
    rule = alert_service.create_rule(
        symbol=request.symbol,
        market=request.market,
        rule_type=request.rule_type,
        threshold=request.threshold,
    )
    return rule.model_dump()


@app.put("/api/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: str, request: UpdateAlertRequest):
    """Update an alert rule."""
    updates = request.model_dump(exclude_none=True)
    rule = alert_service.update_rule(rule_id, updates)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


@app.post("/api/alerts/rules/{rule_id}/toggle")
async def toggle_alert_rule(rule_id: str):
    """Toggle alert rule enabled state."""
    rule = alert_service.toggle_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


@app.delete("/api/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    if alert_service.delete_rule(rule_id):
        return {"message": "Rule deleted"}
    raise HTTPException(status_code=404, detail="Rule not found")


@app.get("/api/alerts/notifications")
async def get_notifications():
    """Get all notifications."""
    notifications = alert_service.get_all_notifications()
    return {"notifications": [n.model_dump() for n in notifications]}


@app.get("/api/alerts/notifications/unread")
async def get_unread_notifications():
    """Get unacknowledged notifications."""
    notifications = alert_service.get_unacknowledged()
    return {"notifications": [n.model_dump() for n in notifications]}


@app.post("/api/alerts/notifications/{notification_id}/acknowledge")
async def acknowledge_notification(notification_id: str):
    """Acknowledge a notification."""
    if alert_service.acknowledge(notification_id):
        return {"message": "Acknowledged"}
    raise HTTPException(status_code=404, detail="Notification not found")


@app.post("/api/alerts/notifications/acknowledge-all")
async def acknowledge_all_notifications():
    """Acknowledge all notifications."""
    count = alert_service.acknowledge_all()
    return {"message": f"Acknowledged {count} notifications"}


# =============================================================================
# PROBABILITY CALCULATOR ENDPOINT
# =============================================================================


@app.get("/api/probability/calculate")
async def calculate_probability(
    current_price: float = Query(...),
    strike: float = Query(...),
    days_to_expiration: int = Query(...),
    iv: float = Query(...),
    symbol: str = Query(default=""),
):
    """Calculate probability of profit and expected move."""
    # Black-Scholes based probability calculation
    t = days_to_expiration / 365.0

    if t <= 0 or iv <= 0:
        raise HTTPException(status_code=400, detail="Invalid parameters")

    # Expected move calculation
    expected_move = current_price * iv * math.sqrt(t)

    # Standard deviation ranges
    one_std_low = current_price - expected_move
    one_std_high = current_price + expected_move
    two_std_low = current_price - (2 * expected_move)
    two_std_high = current_price + (2 * expected_move)

    # Probability calculations using normal distribution approximation
    d = (math.log(current_price / strike) + (0.5 * iv * iv * t)) / (iv * math.sqrt(t))

    # Approximate CDF using error function
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    prob_itm = norm_cdf(d) if strike > current_price else 1 - norm_cdf(d)
    prob_otm = 1 - prob_itm

    return {
        "symbol": symbol,
        "current_price": current_price,
        "strike": strike,
        "days_to_expiration": days_to_expiration,
        "iv": iv,
        "probability_itm": round(prob_itm * 100, 2),
        "probability_otm": round(prob_otm * 100, 2),
        "probability_profit": round(prob_otm * 100, 2),  # For short options
        "expected_move": round(expected_move, 2),
        "one_std_range": [round(one_std_low, 2), round(one_std_high, 2)],
        "two_std_range": [round(two_std_low, 2), round(two_std_high, 2)],
    }


# =============================================================================
# IV HISTORY ENDPOINT
# =============================================================================


@app.get("/api/iv-history/{symbol}")
async def get_iv_history(
    symbol: str,
    market: Market = Query(default="US"),
    days: int = Query(default=90),
):
    """Get historical IV data."""
    import random

    # Generate mock IV history
    data = []
    base_iv = 0.25 + random.uniform(-0.05, 0.05)
    base_price = 100 + random.uniform(-20, 50)

    for i in range(days):
        day_offset = days - i
        d = date.today()
        d = date(d.year, d.month, max(1, d.day - day_offset))

        # Random walk for IV
        base_iv += random.uniform(-0.02, 0.02)
        base_iv = max(0.1, min(0.8, base_iv))

        base_price += random.uniform(-2, 2)
        base_price = max(50, base_price)

        iv_52w_low = base_iv * 0.6
        iv_52w_high = base_iv * 1.5
        iv_rank = ((base_iv - iv_52w_low) / (iv_52w_high - iv_52w_low)) * 100

        data.append({
            "date": str(d),
            "iv": round(base_iv, 4),
            "iv_rank": round(iv_rank, 2),
            "iv_percentile": round(min(100, max(0, iv_rank + random.uniform(-5, 5))), 2),
            "price": round(base_price, 2),
        })

    return {
        "symbol": symbol,
        "market": market,
        "data": data,
    }


# =============================================================================
# TERM STRUCTURE ENDPOINT
# =============================================================================


@app.get("/api/term-structure/{symbol}")
async def get_term_structure(symbol: str, market: Market = Query(default="US")):
    """Get IV term structure across expirations."""
    import random

    # Generate mock term structure
    expirations = [7, 14, 21, 30, 45, 60, 90, 120, 180, 365]
    base_iv = 0.20 + random.uniform(0, 0.1)

    data = []
    for dte in expirations:
        # Term structure typically shows contango (higher IV for longer expirations)
        iv = base_iv * (1 + 0.1 * math.log(dte / 30 + 1)) + random.uniform(-0.02, 0.02)
        data.append({
            "dte": dte,
            "iv": round(max(0.05, iv), 4),
        })

    # Determine if contango or backwardation
    short_term_iv = data[0]["iv"]
    long_term_iv = data[-1]["iv"]
    structure = "contango" if long_term_iv > short_term_iv else "backwardation"

    return {
        "symbol": symbol,
        "market": market,
        "structure": structure,
        "data": data,
    }


# =============================================================================
# SKEW ANALYSIS ENDPOINT
# =============================================================================


@app.get("/api/skew/{symbol}")
async def get_skew_analysis(
    symbol: str,
    market: Market = Query(default="US"),
    expiration: str | None = Query(default=None),
):
    """Get IV skew across strikes."""
    import random

    # Generate mock skew data
    atm_strike = 150
    strikes = [atm_strike + i * 5 for i in range(-10, 11)]

    base_iv = 0.25
    data = []

    for strike in strikes:
        moneyness = (strike - atm_strike) / atm_strike
        # Put skew: lower strikes have higher IV
        skew_adjustment = -0.3 * moneyness if moneyness < 0 else -0.1 * moneyness
        call_iv = base_iv + skew_adjustment + random.uniform(-0.01, 0.01)
        put_iv = base_iv + skew_adjustment * 1.2 + random.uniform(-0.01, 0.01)

        data.append({
            "strike": strike,
            "moneyness": round(moneyness * 100, 2),
            "call_iv": round(max(0.05, call_iv), 4),
            "put_iv": round(max(0.05, put_iv), 4),
        })

    return {
        "symbol": symbol,
        "market": market,
        "atm_strike": atm_strike,
        "expiration": expiration or "nearest",
        "data": data,
    }


# =============================================================================
# EARNINGS CALENDAR ENDPOINT
# =============================================================================


@app.get("/api/earnings")
async def get_earnings_calendar(
    symbols: str = Query(default=""),
    days: int = Query(default=30),
):
    """Get earnings calendar for symbols."""
    import random

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        symbol_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA"]

    events = []
    today = date.today()

    for symbol in symbol_list:
        # Random earnings date within range
        earnings_day = today.day + random.randint(1, days)
        earnings_date = date(today.year, today.month, min(28, earnings_day))

        events.append({
            "symbol": symbol,
            "market": "US",
            "earnings_date": str(earnings_date),
            "time_of_day": random.choice(["before_open", "after_close"]),
            "estimated_eps": round(random.uniform(0.5, 5.0), 2),
            "actual_eps": None,
            "iv_before": round(random.uniform(0.3, 0.6), 4),
            "iv_after": None,
            "iv_crush_percent": None,
            "price_move_percent": None,
        })

    events.sort(key=lambda x: x["earnings_date"])

    return {
        "events": events,
        "start_date": str(today),
        "end_date": str(date(today.year, today.month, min(28, today.day + days))),
    }


# =============================================================================
# CORRELATION MATRIX ENDPOINT
# =============================================================================


@app.get("/api/correlation")
async def get_correlation_matrix(
    symbols: str = Query(default="SPY,QQQ,IWM,DIA"),
    days: int = Query(default=30),
):
    """Get correlation matrix for symbols."""
    import random

    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    n = len(symbol_list)

    # Generate mock correlation matrix
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            elif j < i:
                row.append(matrix[j][i])  # Symmetric
            else:
                # Generate realistic correlations (mostly positive for stocks)
                corr = random.uniform(0.3, 0.9)
                row.append(round(corr, 3))
        matrix.append(row)

    return {
        "symbols": symbol_list,
        "matrix": matrix,
        "period_days": days,
    }


# =============================================================================
# STRESS TESTING ENDPOINT
# =============================================================================


class StressTestRequest(BaseModel):
    price_change_percent: float = -20
    iv_change_percent: float = 50


@app.post("/api/stress-test")
async def run_stress_test(request: StressTestRequest):
    """Run portfolio stress test."""
    positions = position_service.get_open()

    scenario = {
        "name": f"Price {request.price_change_percent:+.0f}%, IV {request.iv_change_percent:+.0f}%",
        "price_change_percent": request.price_change_percent,
        "iv_change_percent": request.iv_change_percent,
    }

    results = []
    total_current = 0
    total_stressed = 0

    for pos in positions:
        current = pos.current_value or pos.entry_cost
        # Simplified stress calculation
        price_impact = current * (request.price_change_percent / 100)
        iv_impact = current * 0.1 * (request.iv_change_percent / 100)  # Vega approximation
        stressed = current + price_impact + iv_impact

        results.append({
            "position_id": pos.id,
            "symbol": pos.symbol,
            "scenario": scenario,
            "current_value": round(current, 2),
            "stressed_value": round(stressed, 2),
            "pnl_impact": round(stressed - current, 2),
            "pnl_impact_percent": round((stressed - current) / current * 100, 2) if current != 0 else 0,
        })

        total_current += current
        total_stressed += stressed

    return {
        "scenario": scenario,
        "results": results,
        "total_current_value": round(total_current, 2),
        "total_stressed_value": round(total_stressed, 2),
        "total_pnl_impact": round(total_stressed - total_current, 2),
        "total_pnl_impact_percent": round((total_stressed - total_current) / total_current * 100, 2) if total_current != 0 else 0,
    }


@app.get("/api/stress-test/scenarios")
async def get_stress_scenarios():
    """Get predefined stress test scenarios."""
    return {
        "scenarios": [
            {"name": "Market Crash", "price_change_percent": -20, "iv_change_percent": 100},
            {"name": "Flash Crash", "price_change_percent": -10, "iv_change_percent": 50},
            {"name": "Mild Correction", "price_change_percent": -5, "iv_change_percent": 25},
            {"name": "Rally", "price_change_percent": 10, "iv_change_percent": -20},
            {"name": "Strong Rally", "price_change_percent": 20, "iv_change_percent": -30},
            {"name": "Vol Spike", "price_change_percent": 0, "iv_change_percent": 50},
            {"name": "Vol Crush", "price_change_percent": 0, "iv_change_percent": -30},
        ]
    }


# =============================================================================
# JPM VOLATILITY RESEARCH ENDPOINTS
# =============================================================================


@app.get("/api/jpm/report")
async def get_jpm_report():
    """Get JPM volatility research report metadata."""
    return jpm_research_service.get_metadata().model_dump()


@app.get("/api/jpm/trading-candidates")
async def get_jpm_trading_candidates(
    strategy: JPMStrategyType | None = Query(default=None),
):
    """Get JPM trading candidates, optionally filtered by strategy."""
    candidates = jpm_research_service.get_trading_candidates(strategy)
    return {"candidates": [c.model_dump() for c in candidates]}


@app.get("/api/jpm/volatility-screen")
async def get_jpm_volatility_screen(
    screen_type: JPMScreenType | None = Query(default=None),
):
    """Get JPM volatility screen results."""
    screens = jpm_research_service.get_volatility_screen(screen_type)
    return {"screens": [s.model_dump() for s in screens]}


@app.get("/api/jpm/stocks")
async def get_jpm_stocks(
    sort_by: str = Query(default="ticker"),
    ascending: bool = Query(default=True),
    sector: str | None = Query(default=None),
    iv_percentile_min: float | None = Query(default=None),
    iv_percentile_max: float | None = Query(default=None),
):
    """Get all JPM stock data with filtering and sorting."""
    stocks = jpm_research_service.get_all_stocks(
        sort_by=sort_by,
        ascending=ascending,
        sector=sector,
        iv_percentile_min=iv_percentile_min,
        iv_percentile_max=iv_percentile_max,
    )
    return {"stocks": [s.model_dump() for s in stocks], "total": len(stocks)}


@app.get("/api/jpm/stock/{ticker}")
async def get_jpm_stock(ticker: str):
    """Get JPM data for a single stock."""
    stock = jpm_research_service.get_stock(ticker)
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock.model_dump()


@app.get("/api/jpm/full")
async def get_jpm_full_research():
    """Get complete JPM research data."""
    data = jpm_research_service.get_full_research_data()
    return data.model_dump()


# =============================================================================
# FEAR/GREED INDEX ENDPOINT
# =============================================================================


@app.get("/api/fear-greed")
async def get_fear_greed_index():
    """Get market Fear/Greed index from CNN data."""
    import httpx

    CNN_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                CNN_API_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                }
            )
            response.raise_for_status()
            data = response.json()

        # Extract current score and rating
        fear_greed = data.get("fear_and_greed", {})
        score = fear_greed.get("score", 50)
        rating = fear_greed.get("rating", "Neutral")

        # Map CNN rating to our classification
        rating_map = {
            "extreme fear": "Extreme Fear",
            "fear": "Fear",
            "neutral": "Neutral",
            "greed": "Greed",
            "extreme greed": "Extreme Greed",
        }
        classification = rating_map.get(rating.lower(), rating.title())

        # Extract previous values
        previous_close = fear_greed.get("previous_close", score)
        week_ago = fear_greed.get("previous_1_week", score)
        month_ago = fear_greed.get("previous_1_month", score)
        year_ago = fear_greed.get("previous_1_year", score)

        # Extract component scores from CNN data
        component_map = {
            "market_momentum": {
                "key": "market_momentum_sp500",
                "name": "Market Momentum",
                "description": "S&P 500 vs 125-day moving average",
            },
            "stock_price_strength": {
                "key": "stock_price_strength",
                "name": "Stock Price Strength",
                "description": "52-week highs vs lows",
            },
            "stock_price_breadth": {
                "key": "stock_price_breadth",
                "name": "Stock Price Breadth",
                "description": "Advancing vs declining volume",
            },
            "put_call_ratio": {
                "key": "put_call_options",
                "name": "Put/Call Options",
                "description": "5-day put/call ratio",
            },
            "market_volatility": {
                "key": "market_volatility_vix",
                "name": "Market Volatility",
                "description": "VIX vs 50-day average",
            },
            "safe_haven_demand": {
                "key": "safe_haven_demand",
                "name": "Safe Haven Demand",
                "description": "Stocks vs bonds performance",
            },
            "junk_bond_demand": {
                "key": "junk_bond_demand",
                "name": "Junk Bond Demand",
                "description": "Spread vs investment grade",
            },
        }

        components = {}
        for comp_id, comp_info in component_map.items():
            cnn_key = comp_info["key"]
            cnn_data = data.get(cnn_key, {})
            components[comp_id] = {
                "name": comp_info["name"],
                "description": comp_info["description"],
                "score": round(cnn_data.get("score", 50), 1),
                "rating": cnn_data.get("rating", "Neutral"),
            }

        return {
            "score": round(score, 1),
            "classification": classification,
            "previous_close": round(previous_close, 1),
            "week_ago": round(week_ago, 1),
            "month_ago": round(month_ago, 1),
            "year_ago": round(year_ago, 1),
            "components": components,
            "timestamp": datetime.now().isoformat(),
            "source": "CNN Fear & Greed Index",
        }

    except Exception as e:
        # Fallback to mock data if CNN API fails
        import random

        components = {
            "market_momentum": {
                "name": "Market Momentum",
                "description": "S&P 500 vs 125-day moving average",
                "score": round(random.uniform(20, 80), 1),
            },
            "stock_price_strength": {
                "name": "Stock Price Strength",
                "description": "52-week highs vs lows",
                "score": round(random.uniform(25, 75), 1),
            },
            "stock_price_breadth": {
                "name": "Stock Price Breadth",
                "description": "Advancing vs declining volume",
                "score": round(random.uniform(30, 70), 1),
            },
            "put_call_ratio": {
                "name": "Put/Call Options",
                "description": "5-day put/call ratio",
                "score": round(random.uniform(20, 80), 1),
            },
            "market_volatility": {
                "name": "Market Volatility",
                "description": "VIX vs 50-day average",
                "score": round(random.uniform(25, 75), 1),
            },
            "safe_haven_demand": {
                "name": "Safe Haven Demand",
                "description": "Stocks vs bonds performance",
                "score": round(random.uniform(30, 70), 1),
            },
            "junk_bond_demand": {
                "name": "Junk Bond Demand",
                "description": "Spread vs investment grade",
                "score": round(random.uniform(25, 75), 1),
            },
        }

        total_score = sum(c["score"] for c in components.values()) / len(components)

        if total_score < 25:
            classification = "Extreme Fear"
        elif total_score < 45:
            classification = "Fear"
        elif total_score < 55:
            classification = "Neutral"
        elif total_score < 75:
            classification = "Greed"
        else:
            classification = "Extreme Greed"

        return {
            "score": round(total_score, 1),
            "classification": classification,
            "previous_close": round(total_score + random.uniform(-5, 5), 1),
            "week_ago": round(total_score + random.uniform(-10, 10), 1),
            "month_ago": round(total_score + random.uniform(-15, 15), 1),
            "year_ago": round(total_score + random.uniform(-20, 20), 1),
            "components": components,
            "timestamp": datetime.now().isoformat(),
            "source": "Mock (CNN API unavailable)",
            "error": str(e),
        }


# =============================================================================
# MARKET INDICATORS ENDPOINT
# =============================================================================

# Sector ETF definitions
SECTOR_ETFS = [
    ("XLF", "Financials"),
    ("XLK", "Technology"),
    ("XLE", "Energy"),
    ("XLV", "Healthcare"),
    ("XLI", "Industrials"),
    ("XLU", "Utilities"),
    ("XLP", "Consumer Staples"),
    ("XLY", "Consumer Disc."),
    ("XLB", "Materials"),
    ("XLRE", "Real Estate"),
    ("XLC", "Communications"),
]


@app.get("/api/market-indicators")
async def get_market_indicators():
    """Get comprehensive market indicators (bonds, commodities, sectors, breadth)."""
    import random

    provider = get_provider()
    now = datetime.now()

    # Fetch bond/rate data
    try:
        tnx_quote = await provider.get_quote("^TNX", "US")
        tnx_yield = tnx_quote.price
    except Exception:
        tnx_yield = 4.25 + random.uniform(-0.2, 0.2)

    try:
        irx_quote = await provider.get_quote("^IRX", "US")
        irx_yield = irx_quote.price / 100  # IRX is in basis points
    except Exception:
        irx_yield = 4.50 + random.uniform(-0.2, 0.2)

    try:
        tlt_quote = await provider.get_quote("TLT", "US")
        tlt_price = tlt_quote.price
        tlt_change = tlt_quote.change
        tlt_change_percent = tlt_quote.change_percent
    except Exception:
        tlt_price = 92.50 + random.uniform(-2, 2)
        tlt_change = random.uniform(-1, 1)
        tlt_change_percent = (tlt_change / tlt_price) * 100

    yield_spread = tnx_yield - irx_yield

    bonds = BondRatesData(
        tnx_yield=round(tnx_yield, 3),
        irx_yield=round(irx_yield, 3),
        yield_spread=round(yield_spread, 3),
        tlt_price=round(tlt_price, 2),
        tlt_change=round(tlt_change, 2) if tlt_change else None,
        tlt_change_percent=round(tlt_change_percent, 2) if tlt_change_percent else None,
        timestamp=now,
    )

    # Fetch commodity data
    try:
        gld_quote = await provider.get_quote("GLD", "US")
        gold_price = gld_quote.price
        gold_change = gld_quote.change
        gold_change_percent = gld_quote.change_percent
    except Exception:
        gold_price = 185.0 + random.uniform(-3, 3)
        gold_change = random.uniform(-2, 2)
        gold_change_percent = (gold_change / gold_price) * 100

    try:
        uso_quote = await provider.get_quote("USO", "US")
        oil_price = uso_quote.price
        oil_change = uso_quote.change
        oil_change_percent = uso_quote.change_percent
    except Exception:
        oil_price = 72.0 + random.uniform(-2, 2)
        oil_change = random.uniform(-1.5, 1.5)
        oil_change_percent = (oil_change / oil_price) * 100

    try:
        uup_quote = await provider.get_quote("UUP", "US")
        dollar_price = uup_quote.price
        dollar_change = uup_quote.change
        dollar_change_percent = uup_quote.change_percent
    except Exception:
        dollar_price = 28.0 + random.uniform(-0.5, 0.5)
        dollar_change = random.uniform(-0.3, 0.3)
        dollar_change_percent = (dollar_change / dollar_price) * 100

    commodities = CommoditiesData(
        gold_price=round(gold_price, 2),
        gold_change=round(gold_change, 2) if gold_change else None,
        gold_change_percent=round(gold_change_percent, 2) if gold_change_percent else None,
        oil_price=round(oil_price, 2),
        oil_change=round(oil_change, 2) if oil_change else None,
        oil_change_percent=round(oil_change_percent, 2) if oil_change_percent else None,
        dollar_price=round(dollar_price, 2),
        dollar_change=round(dollar_change, 2) if dollar_change else None,
        dollar_change_percent=round(dollar_change_percent, 2) if dollar_change_percent else None,
        timestamp=now,
    )

    # Fetch sector data
    sectors = []
    for symbol, name in SECTOR_ETFS:
        try:
            quote = await provider.get_quote(symbol, "US")
            sectors.append(SectorData(
                symbol=symbol,
                name=name,
                price=round(quote.price, 2),
                change=round(quote.change, 2) if quote.change else None,
                change_percent=round(quote.change_percent, 2) if quote.change_percent else None,
            ))
        except Exception:
            # Mock data fallback
            base_price = 40 + random.uniform(0, 60)
            change_pct = random.uniform(-3, 3)
            sectors.append(SectorData(
                symbol=symbol,
                name=name,
                price=round(base_price, 2),
                change=round(base_price * change_pct / 100, 2),
                change_percent=round(change_pct, 2),
            ))

    # Market breadth data (simulated - real data requires paid sources)
    # Using random but realistic values
    advances = random.randint(1200, 2200)
    declines = random.randint(800, 1800)
    new_highs = random.randint(20, 150)
    new_lows = random.randint(10, 100)

    breadth = MarketBreadthData(
        advances=advances,
        declines=declines,
        advance_decline_ratio=round(advances / max(declines, 1), 2),
        new_highs=new_highs,
        new_lows=new_lows,
        highs_lows_ratio=round(new_highs / max(new_lows, 1), 2),
        mcclellan_oscillator=round(random.uniform(-100, 100), 1),
        timestamp=now,
    )

    response = MarketIndicatorsResponse(
        bonds=bonds,
        commodities=commodities,
        sectors=sectors,
        breadth=breadth,
        timestamp=now,
    )

    return response.model_dump()


# ══════════════════════════════════════════════════════════════════════════
# DECISION ENGINE ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════

from mcp_server.services.engine import DecisionEngine

_engine = DecisionEngine()


class EngineAnalysisRequest(BaseModel):
    nav: float = 100_000
    objective: str = "income"
    positions: list[dict] | None = None


class EngineRecommendRequest(BaseModel):
    nav: float = 100_000
    objective: str = "income"


class PositionEvalRequest(BaseModel):
    position: dict


class PostTradeReviewRequest(BaseModel):
    trade_id: str
    entry_date: str
    exit_date: str | None = None
    strategy: str
    gross_pnl: float = 0.0
    pnl_pct: float = 0.0
    what_worked: str = ""
    what_failed: str = ""


@app.get("/api/engine/regime")
async def get_engine_regime():
    """Get current market regime classification."""
    regime = await _engine.get_regime()
    return regime.model_dump()


@app.get("/api/engine/regime/history")
async def get_engine_regime_history():
    """Get regime history (current + previous)."""
    current = await _engine.get_regime()
    result = {"current": current.model_dump(), "previous": None}
    if _engine._previous_regime:
        result["previous"] = _engine._previous_regime.model_dump()
    return result


@app.post("/api/engine/recommend")
async def get_engine_recommendations(req: EngineRecommendRequest):
    """Get strategy recommendations for current market conditions."""
    rec = await _engine.get_recommendations(req.nav, req.objective)
    return rec.model_dump()


@app.post("/api/engine/analysis")
async def get_engine_analysis(req: EngineAnalysisRequest):
    """Run the full decision engine pipeline."""
    result = await _engine.full_analysis(req.nav, req.objective, req.positions)
    return result.model_dump()


@app.get("/api/engine/strategies")
async def get_engine_strategies():
    """Get the complete strategy universe catalog."""
    strategies = _engine.get_strategy_universe()
    return [s.model_dump() for s in strategies]


@app.get("/api/engine/strategies/{family}")
async def get_engine_strategies_by_family(family: str):
    """Get strategies filtered by family."""
    try:
        strategies = _engine.get_strategies_by_family(family)
        return [s.model_dump() for s in strategies]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/engine/tail-risk")
async def get_engine_tail_risk():
    """Get current tail risk assessment."""
    assessment = await _engine.get_tail_risk()
    return assessment.model_dump()


@app.get("/api/engine/early-warnings")
async def get_engine_early_warnings():
    """Get active early warning signals."""
    assessment = await _engine.get_tail_risk()
    return {
        "warnings": [w.model_dump() for w in assessment.early_warnings],
        "active_count": assessment.active_warnings_count,
        "crisis_active": assessment.crisis_protocol_active,
    }


@app.get("/api/engine/conflicts")
async def get_engine_conflicts():
    """Get all signal conflicts with detection status."""
    conflicts = await _engine.get_all_conflicts()
    return [c.model_dump() for c in conflicts]


@app.get("/api/engine/conflicts/active")
async def get_engine_active_conflicts():
    """Get only currently detected signal conflicts."""
    conflicts = await _engine.get_conflicts()
    return [c.model_dump() for c in conflicts]


@app.post("/api/engine/positions/evaluate")
async def evaluate_engine_position(req: PositionEvalRequest):
    """Evaluate a single position against adjustment and exit rules."""
    health = await _engine.evaluate_position(req.position)
    return health.model_dump()


@app.get("/api/engine/playbook/{event_type}")
async def get_engine_playbook(event_type: str):
    """Get an event-specific playbook (FOMC, EARNINGS, CPI, NFP)."""
    try:
        playbook = _engine.get_playbook(event_type)
        return playbook.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/engine/playbook/0dte/info")
async def get_engine_zero_dte():
    """Get the 0DTE playbook."""
    playbook = _engine.get_zero_dte_playbook()
    return playbook.model_dump()


@app.get("/api/engine/playbook/0dte/{day}")
async def get_engine_zero_dte_day(day: str):
    """Get 0DTE recommendation for a specific day of the week."""
    try:
        info = _engine.get_zero_dte_day(day)
        return info.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/engine/reference")
async def list_engine_reference_tables():
    """List all available reference tables."""
    return {"tables": _engine.list_reference_tables()}


@app.get("/api/engine/reference/{table_name}")
async def get_engine_reference_table(table_name: str):
    """Get a specific reference data table."""
    try:
        data = _engine.get_reference_table(table_name)
        return [item.model_dump() for item in data]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/engine/review")
async def create_post_trade_review(req: PostTradeReviewRequest):
    """Create a post-trade review record."""
    from mcp_server.engine_models import PostTradeReview, PnLAttribution
    regime = await _engine.get_regime()
    review = PostTradeReview(
        trade_id=req.trade_id,
        entry_date=datetime.strptime(req.entry_date, "%Y-%m-%d").date(),
        exit_date=datetime.strptime(req.exit_date, "%Y-%m-%d").date() if req.exit_date else None,
        strategy=req.strategy,
        regime_at_entry=regime,
        gross_pnl=req.gross_pnl,
        pnl_pct=req.pnl_pct,
        what_worked=req.what_worked,
        what_failed=req.what_failed,
    )
    return review.model_dump()
