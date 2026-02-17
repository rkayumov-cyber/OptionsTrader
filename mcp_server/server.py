"""MCP server for cross-market equities options platform."""

import asyncio
import json
from datetime import datetime
from typing import Literal

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)
from pydantic import BaseModel

from mcp_server.models import Market, MarketInfo, WatchlistItem
from mcp_server.providers.base import MarketDataProvider
from mcp_server.providers.mock import MockProvider
from mcp_server.providers.yahoo import YahooProvider
from mcp_server.providers.ibkr import IBKRProvider
from mcp_server.providers.saxo import SAXOProvider
from mcp_server.services.jpm_research import JPMResearchService
from mcp_server.services.engine import DecisionEngine


# Initialize server
server = Server("options-trader")

# Provider registry - initialize available providers
providers: dict[str, MarketDataProvider] = {
    "mock": MockProvider(),
    "yahoo": YahooProvider(),
}
active_provider_name: str = "mock"

# In-memory watchlist
watchlist: list[WatchlistItem] = []

# JPM Research Service
jpm_research = JPMResearchService()

# Decision Engine
_decision_engine = DecisionEngine()


def get_provider() -> MarketDataProvider:
    """Get active provider."""
    return providers[active_provider_name]


def switch_provider(name: str, **kwargs) -> tuple[bool, str]:
    """Switch to a different provider."""
    global active_provider_name

    name = name.lower()

    if name in providers:
        active_provider_name = name
        return True, f"Switched to {name} provider"

    # Initialize IBKR provider on-demand (requires connection params)
    if name == "ibkr":
        try:
            ibkr = IBKRProvider(
                host=kwargs.get("host") or "127.0.0.1",
                port=kwargs.get("port") or 7497,
                client_id=kwargs.get("client_id") or 1,
            )
            providers["ibkr"] = ibkr
            active_provider_name = "ibkr"
            return True, "Switched to IBKR provider (will connect on first request)"
        except Exception as e:
            return False, f"Failed to initialize IBKR provider: {e}"

    # Initialize SAXO provider on-demand (requires OAuth token)
    if name == "saxo":
        access_token = kwargs.get("access_token")
        if not access_token:
            return False, "SAXO provider requires access_token parameter"
        try:
            saxo = SAXOProvider(
                access_token=access_token,
                environment=kwargs.get("environment") or "sim",
            )
            providers["saxo"] = saxo
            active_provider_name = "saxo"
            env = kwargs.get("environment") or "sim"
            return True, f"Switched to SAXO provider ({env} environment)"
        except Exception as e:
            return False, f"Failed to initialize SAXO provider: {e}"

    return False, f"Unknown provider: {name}. Available: {', '.join(providers.keys())}, ibkr, saxo"


# Market information
MARKETS: dict[Market, MarketInfo] = {
    "US": MarketInfo(
        code="US",
        name="United States",
        currency="USD",
        timezone="America/New_York",
        trading_hours="09:30-16:00 ET",
    ),
    "JP": MarketInfo(
        code="JP",
        name="Japan",
        currency="JPY",
        timezone="Asia/Tokyo",
        trading_hours="09:00-15:00 JST",
    ),
    "HK": MarketInfo(
        code="HK",
        name="Hong Kong",
        currency="HKD",
        timezone="Asia/Hong_Kong",
        trading_hours="09:30-16:00 HKT",
    ),
}


# =============================================================================
# TOOLS
# =============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_quote",
            description="Get real-time price quote for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol (e.g., AAPL, 7203.T, 0700.HK)",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "JP", "HK"],
                        "description": "Market identifier",
                    },
                },
                "required": ["symbol", "market"],
            },
        ),
        Tool(
            name="get_option_chain",
            description="Get option chain with calls and puts for a symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Underlying ticker symbol",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "JP", "HK"],
                        "description": "Market identifier",
                    },
                    "expiration": {
                        "type": "string",
                        "description": "Specific expiration date (YYYY-MM-DD), optional",
                    },
                },
                "required": ["symbol", "market"],
            },
        ),
        Tool(
            name="get_volatility_surface",
            description="Get implied volatility surface across strikes and expirations",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Underlying ticker symbol",
                    },
                    "market": {
                        "type": "string",
                        "enum": ["US", "JP", "HK"],
                        "description": "Market identifier",
                    },
                },
                "required": ["symbol", "market"],
            },
        ),
        Tool(
            name="add_to_watchlist",
            description="Add a symbol to the watchlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "market": {
                        "type": "string",
                        "enum": ["US", "JP", "HK"],
                        "description": "Market identifier",
                    },
                    "name": {"type": "string", "description": "Optional display name"},
                },
                "required": ["symbol", "market"],
            },
        ),
        Tool(
            name="remove_from_watchlist",
            description="Remove a symbol from the watchlist",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Ticker symbol"},
                    "market": {
                        "type": "string",
                        "enum": ["US", "JP", "HK"],
                        "description": "Market identifier",
                    },
                },
                "required": ["symbol", "market"],
            },
        ),
        Tool(
            name="list_providers",
            description="List available data providers and show which one is active",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="switch_provider",
            description="Switch to a different market data provider",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "enum": ["mock", "yahoo", "ibkr", "saxo"],
                        "description": "Provider name",
                    },
                    "host": {
                        "type": "string",
                        "description": "IBKR TWS/Gateway host (default: 127.0.0.1)",
                    },
                    "port": {
                        "type": "integer",
                        "description": "IBKR TWS/Gateway port (7497=paper, 7496=live)",
                    },
                    "client_id": {
                        "type": "integer",
                        "description": "IBKR client ID (default: 1)",
                    },
                    "access_token": {
                        "type": "string",
                        "description": "SAXO OAuth2 access token (required for SAXO)",
                    },
                    "environment": {
                        "type": "string",
                        "enum": ["sim", "live"],
                        "description": "SAXO environment (default: sim)",
                    },
                },
                "required": ["provider"],
            },
        ),
        # JPM Research Tools
        Tool(
            name="get_jpm_trading_candidates",
            description="Get JPM options trading candidates by strategy type (call_overwriting, call_buying, put_underwriting, put_buying)",
            inputSchema={
                "type": "object",
                "properties": {
                    "strategy": {
                        "type": "string",
                        "enum": ["call_overwriting", "call_buying", "put_underwriting", "put_buying"],
                        "description": "Strategy type to filter candidates",
                    },
                },
                "required": ["strategy"],
            },
        ),
        Tool(
            name="get_jpm_volatility_screen",
            description="Get JPM volatility screen results (rich_iv, cheap_iv, iv_top_movers, iv_bottom_movers)",
            inputSchema={
                "type": "object",
                "properties": {
                    "screen_type": {
                        "type": "string",
                        "enum": ["rich_iv", "cheap_iv", "iv_top_movers", "iv_bottom_movers"],
                        "description": "Type of volatility screen",
                    },
                },
                "required": ["screen_type"],
            },
        ),
        Tool(
            name="get_jpm_stock_data",
            description="Get JPM research data for a specific stock symbol",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., AAPL, MSFT)",
                    },
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_jpm_summary",
            description="Get summary of all JPM research recommendations and market overview",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="search_jpm_stocks",
            description="Search JPM stock data with filters (IV rank, sector, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "iv_percentile_min": {
                        "type": "number",
                        "description": "Minimum IV percentile (0-100)",
                    },
                    "iv_percentile_max": {
                        "type": "number",
                        "description": "Maximum IV percentile (0-100)",
                    },
                    "sector": {
                        "type": "string",
                        "description": "Filter by sector (e.g., Technology, Healthcare)",
                    },
                    "has_iv_hv_spread": {
                        "type": "boolean",
                        "description": "Only include stocks with IV > HV (true) or IV < HV (false)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                    },
                },
            },
        ),
        # ═══ DECISION ENGINE TOOLS ═══
        Tool(
            name="get_market_regime",
            description="Classify the current market regime (Crisis/Liquidity Stress/Event/Vol Level+Trend). Returns regime, trend, confidence, event state, and recommended actions.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_strategy_recommendations",
            description="Run the strategy selector engine to get top-3 parameterized strategy recommendations based on current regime and market conditions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nav": {
                        "type": "number",
                        "description": "Portfolio NAV in dollars (default: 100000)",
                    },
                    "objective": {
                        "type": "string",
                        "enum": ["income", "directional", "hedging", "event", "relative_value", "tail", "all"],
                        "description": "Strategy objective filter (default: income)",
                    },
                },
            },
        ),
        Tool(
            name="run_full_analysis",
            description="Run the complete decision engine pipeline: regime classification, strategy selection, tail risk assessment, conflict detection, event playbooks, and position health checks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "nav": {
                        "type": "number",
                        "description": "Portfolio NAV in dollars (default: 100000)",
                    },
                    "objective": {
                        "type": "string",
                        "enum": ["income", "directional", "hedging", "event", "relative_value", "tail", "all"],
                        "description": "Strategy objective filter (default: income)",
                    },
                },
            },
        ),
        Tool(
            name="evaluate_position_health",
            description="Check a position against adjustment rules (A1-A9) and exit rules (X1-X7). Returns triggered rules with priority and recommended actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dte": {"type": "integer", "description": "Days to expiration"},
                    "strategy": {"type": "string", "description": "Strategy name (e.g., cash_secured_put, iron_condor)"},
                    "family": {"type": "string", "enum": ["short_premium", "long_premium"], "description": "Strategy family"},
                    "current_delta": {"type": "number", "description": "Current position delta"},
                    "initial_delta": {"type": "number", "description": "Delta at entry"},
                    "unrealized_pnl": {"type": "number", "description": "Current unrealized P&L"},
                    "max_profit": {"type": "number", "description": "Maximum possible profit"},
                    "premium_received": {"type": "number", "description": "Premium received (credit trades)"},
                    "premium_paid": {"type": "number", "description": "Premium paid (debit trades)"},
                },
                "required": ["dte", "strategy", "family"],
            },
        ),
        Tool(
            name="get_tail_risk_assessment",
            description="Evaluate current tail risk: hedge allocation, early warning signals, crisis protocol status, and 3-pillar tail trading signal.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_event_playbook",
            description="Get event-specific trading playbook with timing, strategy, and sizing for each phase.",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": ["FOMC", "EARNINGS", "CPI", "NFP", "0DTE"],
                        "description": "Event type",
                    },
                    "day": {
                        "type": "string",
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                        "description": "Day of week (for 0DTE playbook only)",
                    },
                },
                "required": ["event_type"],
            },
        ),
        Tool(
            name="get_reference_table",
            description="Look up backtested performance data tables from GS and JPM research. Tables: put_selling, overwriting, hedging, sector_sensitivity, global_vol, zero_dte_premium, vol_risk_premium, tail_trading.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "enum": ["put_selling", "overwriting", "hedging", "sector_sensitivity", "global_vol", "zero_dte_premium", "vol_risk_premium", "tail_trading"],
                        "description": "Name of the reference table",
                    },
                },
                "required": ["table_name"],
            },
        ),
        Tool(
            name="resolve_conflict",
            description="Check for conflicting market signals and get resolution rules. Detects 8 conflict scenarios from the GS/JPM conflict matrix.",
            inputSchema={
                "type": "object",
                "properties": {
                    "show_all": {
                        "type": "boolean",
                        "description": "If true, show all 8 scenarios with status. If false (default), show only detected conflicts.",
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    global watchlist
    provider = get_provider()

    if name == "get_quote":
        quote = await provider.get_quote(arguments["symbol"], arguments["market"])
        return [TextContent(type="text", text=quote.model_dump_json(indent=2))]

    elif name == "get_option_chain":
        chain = await provider.get_option_chain(
            arguments["symbol"],
            arguments["market"],
            arguments.get("expiration"),
        )
        # Return summary to avoid overwhelming output
        summary = {
            "underlying": chain.underlying,
            "market": chain.market,
            "expirations": [str(e) for e in chain.expirations],
            "num_calls": len(chain.calls),
            "num_puts": len(chain.puts),
            "calls_sample": [c.model_dump() for c in chain.calls[:5]],
            "puts_sample": [p.model_dump() for p in chain.puts[:5]],
            "timestamp": chain.timestamp.isoformat(),
        }
        return [TextContent(type="text", text=json.dumps(summary, indent=2, default=str))]

    elif name == "get_volatility_surface":
        surface = await provider.get_volatility_surface(
            arguments["symbol"], arguments["market"]
        )
        return [TextContent(type="text", text=surface.model_dump_json(indent=2))]

    elif name == "add_to_watchlist":
        item = WatchlistItem(
            symbol=arguments["symbol"],
            market=arguments["market"],
            name=arguments.get("name"),
            added_at=datetime.now(),
        )
        watchlist.append(item)
        return [TextContent(type="text", text=f"Added {item.symbol} to watchlist")]

    elif name == "remove_from_watchlist":
        original_len = len(watchlist)
        watchlist = [
            w
            for w in watchlist
            if not (w.symbol == arguments["symbol"] and w.market == arguments["market"])
        ]
        if len(watchlist) < original_len:
            return [TextContent(type="text", text=f"Removed {arguments['symbol']} from watchlist")]
        return [TextContent(type="text", text=f"{arguments['symbol']} not found in watchlist")]

    elif name == "list_providers":
        provider_info = {
            "active": active_provider_name,
            "available": [
                {
                    "name": name,
                    "markets": p.supported_markets,
                    "active": name == active_provider_name,
                }
                for name, p in providers.items()
            ],
            "note": "IBKR requires TWS/Gateway connection. SAXO requires OAuth2 access token.",
        }
        return [TextContent(type="text", text=json.dumps(provider_info, indent=2))]

    elif name == "switch_provider":
        success, message = switch_provider(
            arguments["provider"],
            host=arguments.get("host"),
            port=arguments.get("port"),
            client_id=arguments.get("client_id"),
            access_token=arguments.get("access_token"),
            environment=arguments.get("environment"),
        )
        return [TextContent(type="text", text=message)]

    # JPM Research Tool Handlers
    elif name == "get_jpm_trading_candidates":
        candidates = jpm_research.get_trading_candidates(arguments["strategy"])
        return [TextContent(type="text", text=json.dumps(
            [c.model_dump() for c in candidates],
            indent=2,
            default=str,
        ))]

    elif name == "get_jpm_volatility_screen":
        screen_results = jpm_research.get_volatility_screen(arguments["screen_type"])
        return [TextContent(type="text", text=json.dumps(
            [s.model_dump() for s in screen_results],
            indent=2,
            default=str,
        ))]

    elif name == "get_jpm_stock_data":
        stock = jpm_research.get_stock(arguments["symbol"])
        if stock:
            # Also get any strategy candidates for this symbol
            candidates = jpm_research.get_candidates_for_symbol(arguments["symbol"])
            result = {
                "stock_data": stock.model_dump(),
                "strategy_candidates": [c.model_dump() for c in candidates],
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        return [TextContent(type="text", text=json.dumps(
            {"error": f"Stock {arguments['symbol']} not found in JPM research data"},
            indent=2,
        ))]

    elif name == "get_jpm_summary":
        summary = jpm_research.get_summary()
        return [TextContent(type="text", text=json.dumps(summary, indent=2, default=str))]

    elif name == "search_jpm_stocks":
        all_stocks = jpm_research.get_all_stocks()
        filtered = all_stocks

        # Apply filters
        if "iv_percentile_min" in arguments and arguments["iv_percentile_min"] is not None:
            filtered = [s for s in filtered if s.iv_percentile >= arguments["iv_percentile_min"]]
        if "iv_percentile_max" in arguments and arguments["iv_percentile_max"] is not None:
            filtered = [s for s in filtered if s.iv_percentile <= arguments["iv_percentile_max"]]
        if "sector" in arguments and arguments["sector"] is not None:
            sector_lower = arguments["sector"].lower()
            filtered = [s for s in filtered if s.sector and sector_lower in s.sector.lower()]
        if "has_iv_hv_spread" in arguments and arguments["has_iv_hv_spread"] is not None:
            if arguments["has_iv_hv_spread"]:
                filtered = [s for s in filtered if s.iv_hv_spread and s.iv_hv_spread > 0]
            else:
                filtered = [s for s in filtered if s.iv_hv_spread and s.iv_hv_spread < 0]

        # Apply limit
        limit = arguments.get("limit", 20) or 20
        filtered = filtered[:limit]

        return [TextContent(type="text", text=json.dumps(
            [s.model_dump() for s in filtered],
            indent=2,
            default=str,
        ))]

    # ═══ DECISION ENGINE TOOL HANDLERS ═══
    elif name == "get_market_regime":
        regime = await _decision_engine.get_regime()
        return [TextContent(type="text", text=json.dumps(regime.model_dump(), indent=2, default=str))]

    elif name == "get_strategy_recommendations":
        nav = arguments.get("nav", 100_000)
        objective = arguments.get("objective", "income")
        rec = await _decision_engine.get_recommendations(nav, objective)
        return [TextContent(type="text", text=json.dumps(rec.model_dump(), indent=2, default=str))]

    elif name == "run_full_analysis":
        nav = arguments.get("nav", 100_000)
        objective = arguments.get("objective", "income")
        result = await _decision_engine.full_analysis(nav, objective)
        return [TextContent(type="text", text=json.dumps(result.model_dump(), indent=2, default=str))]

    elif name == "evaluate_position_health":
        position = {
            "id": "eval",
            "dte": arguments.get("dte", 30),
            "strategy": arguments.get("strategy", ""),
            "family": arguments.get("family", "short_premium"),
            "current_delta": arguments.get("current_delta", 15),
            "initial_delta": arguments.get("initial_delta", 15),
            "unrealized_pnl": arguments.get("unrealized_pnl", 0),
            "max_profit": arguments.get("max_profit", 0),
            "premium_received": arguments.get("premium_received", 0),
            "premium_paid": arguments.get("premium_paid", 0),
        }
        health = await _decision_engine.evaluate_position(position)
        return [TextContent(type="text", text=json.dumps(health.model_dump(), indent=2, default=str))]

    elif name == "get_tail_risk_assessment":
        assessment = await _decision_engine.get_tail_risk()
        return [TextContent(type="text", text=json.dumps(assessment.model_dump(), indent=2, default=str))]

    elif name == "get_event_playbook":
        event_type = arguments["event_type"]
        if event_type == "0DTE":
            day = arguments.get("day")
            if day:
                info = _decision_engine.get_zero_dte_day(day)
                return [TextContent(type="text", text=json.dumps(info.model_dump(), indent=2, default=str))]
            else:
                playbook = _decision_engine.get_zero_dte_playbook()
                return [TextContent(type="text", text=json.dumps(playbook.model_dump(), indent=2, default=str))]
        else:
            playbook = _decision_engine.get_playbook(event_type)
            return [TextContent(type="text", text=json.dumps(playbook.model_dump(), indent=2, default=str))]

    elif name == "get_reference_table":
        table = _decision_engine.get_reference_table(arguments["table_name"])
        return [TextContent(type="text", text=json.dumps(
            [item.model_dump() for item in table], indent=2, default=str
        ))]

    elif name == "resolve_conflict":
        show_all = arguments.get("show_all", False)
        if show_all:
            conflicts = await _decision_engine.get_all_conflicts()
        else:
            conflicts = await _decision_engine.get_conflicts()
        return [TextContent(type="text", text=json.dumps(
            [c.model_dump() for c in conflicts], indent=2, default=str
        ))]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


# =============================================================================
# RESOURCES
# =============================================================================


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    resources = [
        Resource(
            uri="markets://all",
            name="All Markets",
            description="Information about all supported markets (US, JP, HK)",
            mimeType="application/json",
        ),
        Resource(
            uri="watchlist://default",
            name="Watchlist",
            description="Current watchlist",
            mimeType="application/json",
        ),
        # JPM Research Resources
        Resource(
            uri="jpm://summary",
            name="JPM Research Summary",
            description="Summary of JPM volatility research recommendations (Jan 6, 2026)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://call-overwriting",
            name="JPM Call Overwriting Candidates",
            description="Stocks recommended for covered call strategies (high IV, sell calls)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://call-buying",
            name="JPM Call Buying Candidates",
            description="Stocks recommended for long call strategies (cheap IV, buy calls)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://put-underwriting",
            name="JPM Put Underwriting Candidates",
            description="Stocks recommended for cash-secured put strategies (high IV, sell puts)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://put-buying",
            name="JPM Put Buying Candidates",
            description="Stocks recommended for long put strategies (cheap IV, buy puts)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://rich-iv",
            name="JPM Rich IV Stocks",
            description="Stocks with expensive implied volatility (>75th percentile)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://cheap-iv",
            name="JPM Cheap IV Stocks",
            description="Stocks with cheap implied volatility (<25th percentile)",
            mimeType="application/json",
        ),
        Resource(
            uri="jpm://iv-movers",
            name="JPM IV Movers",
            description="Stocks with largest IV changes (top and bottom movers)",
            mimeType="application/json",
        ),
        # ═══ DECISION ENGINE RESOURCES ═══
        Resource(
            uri="engine://regime",
            name="Current Market Regime",
            description="Current regime classification with trend, confidence, events, and actions",
            mimeType="application/json",
        ),
        Resource(
            uri="engine://strategies",
            name="Strategy Universe",
            description="Complete catalog of 20+ strategy templates from GS/JPM research",
            mimeType="application/json",
        ),
        Resource(
            uri="engine://tail-risk",
            name="Tail Risk Assessment",
            description="Current tail risk: hedge allocation, early warnings, crisis protocol, 3-pillar signal",
            mimeType="application/json",
        ),
        Resource(
            uri="engine://reference-tables",
            name="Reference Tables Index",
            description="Index of 8 backtested performance tables from GS and JPM research",
            mimeType="application/json",
        ),
    ]
    # Add individual market resources
    for code, info in MARKETS.items():
        resources.append(
            Resource(
                uri=f"markets://{code.lower()}",
                name=f"{info.name} Market",
                description=f"Information about {info.name} equity options market",
                mimeType="application/json",
            )
        )
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource."""
    if uri == "markets://all":
        return json.dumps(
            {code: info.model_dump() for code, info in MARKETS.items()},
            indent=2,
        )

    if uri.startswith("markets://"):
        market_code = uri.replace("markets://", "").upper()
        if market_code in MARKETS:
            return MARKETS[market_code].model_dump_json(indent=2)
        return json.dumps({"error": f"Unknown market: {market_code}"})

    if uri == "watchlist://default":
        return json.dumps(
            [w.model_dump() for w in watchlist],
            indent=2,
            default=str,
        )

    # JPM Research Resources
    if uri == "jpm://summary":
        return json.dumps(jpm_research.get_summary(), indent=2, default=str)

    if uri == "jpm://call-overwriting":
        candidates = jpm_research.get_trading_candidates("call_overwriting")
        return json.dumps([c.model_dump() for c in candidates], indent=2, default=str)

    if uri == "jpm://call-buying":
        candidates = jpm_research.get_trading_candidates("call_buying")
        return json.dumps([c.model_dump() for c in candidates], indent=2, default=str)

    if uri == "jpm://put-underwriting":
        candidates = jpm_research.get_trading_candidates("put_underwriting")
        return json.dumps([c.model_dump() for c in candidates], indent=2, default=str)

    if uri == "jpm://put-buying":
        candidates = jpm_research.get_trading_candidates("put_buying")
        return json.dumps([c.model_dump() for c in candidates], indent=2, default=str)

    if uri == "jpm://rich-iv":
        screen = jpm_research.get_volatility_screen("rich_iv")
        return json.dumps([s.model_dump() for s in screen], indent=2, default=str)

    if uri == "jpm://cheap-iv":
        screen = jpm_research.get_volatility_screen("cheap_iv")
        return json.dumps([s.model_dump() for s in screen], indent=2, default=str)

    if uri == "jpm://iv-movers":
        top = jpm_research.get_volatility_screen("iv_top_movers")
        bottom = jpm_research.get_volatility_screen("iv_bottom_movers")
        return json.dumps({
            "top_movers": [s.model_dump() for s in top],
            "bottom_movers": [s.model_dump() for s in bottom],
        }, indent=2, default=str)

    # ═══ DECISION ENGINE RESOURCES ═══
    if uri == "engine://regime":
        regime = await _decision_engine.get_regime()
        return json.dumps(regime.model_dump(), indent=2, default=str)

    if uri == "engine://strategies":
        strategies = _decision_engine.get_strategy_universe()
        return json.dumps([s.model_dump() for s in strategies], indent=2, default=str)

    if uri == "engine://tail-risk":
        assessment = await _decision_engine.get_tail_risk()
        return json.dumps(assessment.model_dump(), indent=2, default=str)

    if uri == "engine://reference-tables":
        tables = _decision_engine.list_reference_tables()
        return json.dumps({"available_tables": tables}, indent=2)

    return json.dumps({"error": f"Unknown resource: {uri}"})


# =============================================================================
# PROMPTS
# =============================================================================

# JPM Research Prompts
JPM_PROMPTS = {
    "jpm-income": {
        "name": "JPM Income Strategies",
        "description": "JPM-recommended stocks for premium selling (covered calls/cash-secured puts)",
        "template": """Based on J.P. Morgan's US Single Stock Volatility research (January 6, 2026), analyze income-generating options strategies.

Use the get_jpm_trading_candidates tool to fetch:
1. Call overwriting candidates - stocks suitable for covered call writing
2. Put underwriting candidates - stocks suitable for cash-secured puts

For each recommended ticker:
- Explain why JPM identifies it as a premium-selling opportunity
- Review the IV percentile and IV/HV spread
- Suggest specific strikes and expirations based on the current option chain
- Calculate expected premium income and breakeven levels

Focus on high-probability income strategies with favorable risk/reward profiles.""",
    },
    "jpm-directional": {
        "name": "JPM Directional Strategies",
        "description": "JPM-recommended stocks for directional option buying",
        "template": """Based on J.P. Morgan's US Single Stock Volatility research (January 6, 2026), analyze directional options strategies.

Use the get_jpm_trading_candidates tool to fetch:
1. Call buying candidates - stocks with cheap IV where buying calls is attractive
2. Put buying candidates - stocks with cheap IV where buying puts is attractive

For each recommended ticker:
- Explain why JPM identifies it as a buying opportunity
- Review the IV percentile (cheap volatility = better for buyers)
- Analyze the IV/HV relationship
- Suggest specific strikes and expirations
- Calculate risk/reward scenarios

Focus on stocks where implied volatility appears underpriced relative to expected moves.""",
    },
    "jpm-volatility": {
        "name": "JPM Volatility Analysis",
        "description": "Analyze volatility landscape using JPM screens",
        "template": """Using J.P. Morgan's volatility screens from the January 6, 2026 research report, provide a comprehensive volatility analysis.

Use the get_jpm_volatility_screen tool to fetch:
1. rich_iv - Stocks with expensive implied volatility (>75th percentile)
2. cheap_iv - Stocks with cheap implied volatility (<25th percentile)
3. iv_top_movers - Stocks with biggest IV increases
4. iv_bottom_movers - Stocks with biggest IV decreases

Analysis should include:
- Overall market volatility sentiment
- Sectors with elevated/depressed volatility
- Potential mean-reversion opportunities
- Catalysts driving IV changes (earnings, events)
- Actionable trade ideas based on the screens

This analysis helps identify where volatility is mispriced in the market.""",
    },
    "jpm-stock-analysis": {
        "name": "JPM Single Stock Analysis",
        "description": "Deep dive analysis of a specific stock using JPM data",
        "template": """Perform a comprehensive volatility analysis for {symbol} using J.P. Morgan's research data.

Use the get_jpm_stock_data tool to retrieve:
- Current IV metrics (IV30, IV60, IV90)
- IV percentile and rank
- Historical volatility (HV30, HV60)
- IV/HV spread analysis
- Skew metrics
- Term structure (contango/backwardation)

Analysis should cover:
1. **Volatility Assessment**: Is IV rich or cheap relative to history?
2. **IV/HV Analysis**: Is the market over/under-estimating future volatility?
3. **Skew Analysis**: What does the put/call skew tell us about sentiment?
4. **Term Structure**: What is the volatility term structure signaling?
5. **Strategy Recommendations**: Based on JPM signals, what strategies fit best?

If {symbol} is a JPM trading candidate, explain the specific strategy recommendation and rationale.""",
    },
    "jpm-portfolio": {
        "name": "JPM Portfolio Ideas",
        "description": "Build a diversified options portfolio using JPM recommendations",
        "template": """Using J.P. Morgan's January 6, 2026 volatility research, construct a diversified options portfolio.

Fetch all JPM trading candidates using get_jpm_trading_candidates for each strategy type.

Build a balanced portfolio that includes:
1. **Income Sleeve** (40%):
   - Call overwriting on 2-3 positions (sell premium on high IV stocks)
   - Put underwriting on 2-3 positions (sell premium, willing to own)

2. **Directional Sleeve** (40%):
   - Long calls on 2-3 cheap IV stocks with bullish setups
   - Long puts on 2-3 cheap IV stocks for hedging/bearish views

3. **Volatility Sleeve** (20%):
   - Straddles/strangles on stocks with potential catalyst

For each position:
- Specific ticker and strategy rationale from JPM
- Position sizing recommendation
- Risk parameters and stop levels
- Expected return profile

Ensure sector diversification across the portfolio.""",
    },
}

STRATEGY_PROMPTS = {
    "bullish": {
        "name": "Bullish Strategies",
        "description": "Options strategies for bullish market outlook",
        "template": """Analyze bullish options strategies for {symbol} in the {market} market.

Current market data will be fetched using the get_quote and get_option_chain tools.

Consider these strategies:
1. **Long Call** - Buy call options for leveraged upside exposure
2. **Bull Call Spread** - Buy lower strike call, sell higher strike call
3. **Cash-Secured Put** - Sell put to acquire shares at discount or collect premium
4. **Covered Call** - Own shares + sell call for income (if already holding)

For each applicable strategy:
- Calculate max profit, max loss, and breakeven
- Assess risk/reward ratio
- Consider current implied volatility levels
- Factor in time decay (theta)

Provide specific strike and expiration recommendations based on current option chain data.""",
    },
    "bearish": {
        "name": "Bearish Strategies",
        "description": "Options strategies for bearish market outlook",
        "template": """Analyze bearish options strategies for {symbol} in the {market} market.

Current market data will be fetched using the get_quote and get_option_chain tools.

Consider these strategies:
1. **Long Put** - Buy put options for downside protection or speculation
2. **Bear Put Spread** - Buy higher strike put, sell lower strike put
3. **Bear Call Spread** - Sell lower strike call, buy higher strike call

For each applicable strategy:
- Calculate max profit, max loss, and breakeven
- Assess risk/reward ratio
- Consider current implied volatility levels
- Factor in time decay (theta)

Provide specific strike and expiration recommendations based on current option chain data.""",
    },
    "neutral": {
        "name": "Neutral Strategies",
        "description": "Options strategies for range-bound or neutral outlook",
        "template": """Analyze neutral/range-bound options strategies for {symbol} in the {market} market.

Current market data will be fetched using the get_quote, get_option_chain, and get_volatility_surface tools.

Consider these strategies:
1. **Iron Condor** - Sell OTM put spread + sell OTM call spread
2. **Iron Butterfly** - Sell ATM straddle + buy OTM wings
3. **Calendar Spread** - Sell near-term, buy longer-term same strike
4. **Short Straddle/Strangle** - Sell ATM or OTM call + put (high risk)

For each applicable strategy:
- Calculate max profit, max loss, and breakeven points
- Identify optimal strike selection based on expected range
- Assess probability of profit
- Consider volatility term structure

Provide specific strike and expiration recommendations based on current volatility surface.""",
    },
    "volatile": {
        "name": "High Volatility Strategies",
        "description": "Options strategies expecting large price movement",
        "template": """Analyze volatility strategies for {symbol} in the {market} market.

Current market data will be fetched using the get_quote, get_option_chain, and get_volatility_surface tools.

Consider these strategies:
1. **Long Straddle** - Buy ATM call + put, profit from large move either direction
2. **Long Strangle** - Buy OTM call + put, cheaper than straddle
3. **Back Spread** - Sell 1 ATM, buy 2 OTM (call or put)

For each applicable strategy:
- Calculate breakeven points (upper and lower)
- Assess implied volatility vs historical volatility
- Consider upcoming events (earnings, dividends, etc.)
- Factor in vega exposure

Provide specific strike and expiration recommendations. Note: These strategies benefit from volatility expansion.""",
    },
}


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    prompts = []

    # Strategy prompts (require symbol and market)
    for key, info in STRATEGY_PROMPTS.items():
        prompts.append(
            Prompt(
                name=f"strategy-{key}",
                description=info["description"],
                arguments=[
                    PromptArgument(
                        name="symbol",
                        description="Ticker symbol to analyze",
                        required=True,
                    ),
                    PromptArgument(
                        name="market",
                        description="Market (US, JP, or HK)",
                        required=True,
                    ),
                ],
            )
        )

    # JPM prompts (some require symbol, some don't)
    for key, info in JPM_PROMPTS.items():
        args = []
        if "{symbol}" in info["template"]:
            args.append(
                PromptArgument(
                    name="symbol",
                    description="Ticker symbol to analyze",
                    required=True,
                )
            )
        prompts.append(
            Prompt(
                name=key,
                description=info["description"],
                arguments=args,
            )
        )

    # ═══ DECISION ENGINE PROMPTS ═══
    prompts.append(
        Prompt(
            name="engine-analysis",
            description="Run complete decision engine analysis: regime, strategies, tail risk, conflicts",
            arguments=[
                PromptArgument(name="nav", description="Portfolio NAV in dollars (default: 100000)", required=False),
                PromptArgument(name="objective", description="Strategy objective: income, directional, hedging, event, all (default: income)", required=False),
            ],
        )
    )
    prompts.append(
        Prompt(
            name="engine-position-review",
            description="Review an open position against all adjustment (A1-A9) and exit (X1-X7) rules",
            arguments=[
                PromptArgument(name="strategy", description="Strategy name (e.g., cash_secured_put, iron_condor)", required=True),
                PromptArgument(name="dte", description="Days to expiration", required=True),
            ],
        )
    )
    prompts.append(
        Prompt(
            name="engine-event-preparation",
            description="Get event preparation playbook with timing, strategy, and sizing guidance",
            arguments=[
                PromptArgument(name="event_type", description="Event type: FOMC, EARNINGS, CPI, NFP, 0DTE", required=True),
            ],
        )
    )

    return prompts


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Get a prompt with arguments filled in."""
    args = arguments or {}

    # ═══ Handle Engine prompts ═══
    if name == "engine-analysis":
        nav = args.get("nav", "100000")
        objective = args.get("objective", "income")
        prompt_text = f"""Run a complete decision engine analysis for my options portfolio.

Use the run_full_analysis tool with NAV=${nav} and objective="{objective}".

Then provide a comprehensive briefing covering:
1. **Current Market Regime**: Classification, confidence level, trend, and actions
2. **Top Strategy Recommendations**: Top 3 strategies with scores, parameters, and execution guidance
3. **Tail Risk Status**: Hedge allocation, early warning signals, crisis protocol, 3-pillar signal
4. **Signal Conflicts**: Any conflicting signals and their resolutions
5. **Event Playbook**: Active event playbook if in an event window
6. **Position Health**: Any position adjustments or exits needed

Also reference the appropriate reference tables (get_reference_table) for backtested performance data to support recommendations."""
        return GetPromptResult(
            description=f"Full Engine Analysis (NAV=${nav}, objective={objective})",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    if name == "engine-position-review":
        strategy = args.get("strategy", "cash_secured_put")
        dte = args.get("dte", "30")
        prompt_text = f"""Review my open {strategy} position with {dte} DTE against all trading rules.

Use the evaluate_position_health tool with strategy="{strategy}", dte={dte}, family="short_premium".

Check against:
- **Adjustment Rules (A1-A9)**: Time roll (A1), time close (A2), delta breach (A3), strangle test (A4), delta hedge (A5), vol spike (A6), earnings dodge (A7), regime change (A8), correlation spike (A9)
- **Exit Rules (X1-X7)**: Profit targets (X1/X2), stop losses (X3/X4), time stop (X5), regime exit (X6), daily P&L stop (X7)

Also check get_market_regime for current regime compatibility and get_tail_risk_assessment for any elevated risk.

Provide a clear action plan with priority-ordered recommendations."""
        return GetPromptResult(
            description=f"Position Review: {strategy} ({dte} DTE)",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    if name == "engine-event-preparation":
        event_type = args.get("event_type", "FOMC")
        prompt_text = f"""Prepare for the upcoming {event_type} event.

Use the get_event_playbook tool with event_type="{event_type}" to get the full playbook.
Also use get_market_regime to check current regime and get_tail_risk_assessment for risk status.

Provide a comprehensive event preparation plan covering:
1. **Current Phase**: Where we are in the event timeline (pre-event, event-eve, post-event)
2. **IV Behavior**: Expected implied volatility dynamics
3. **Recommended Strategy**: Specific strategy with parameters for this event phase
4. **Sizing Guidance**: Position sizing adjustments for event risk
5. **Key Rules**: Important trading rules for this event type
6. **Risk Warnings**: Any early warning signals or conflicts to be aware of

If event_type is 0DTE, also check the day-of-week premium data and bias."""
        return GetPromptResult(
            description=f"Event Preparation: {event_type}",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=prompt_text))],
        )

    # Handle JPM prompts
    if name in JPM_PROMPTS:
        template = JPM_PROMPTS[name]["template"]
        symbol = args.get("symbol", "AAPL")
        filled_prompt = template.format(symbol=symbol) if "{symbol}" in template else template
        description = JPM_PROMPTS[name]["name"]
        if "{symbol}" in template:
            description = f"{description} for {symbol}"
        return GetPromptResult(
            description=description,
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=filled_prompt),
                )
            ],
        )

    # Handle strategy prompts
    if not name.startswith("strategy-"):
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=f"Unknown prompt: {name}"),
                )
            ]
        )

    strategy_key = name.replace("strategy-", "")
    if strategy_key not in STRATEGY_PROMPTS:
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=f"Unknown strategy: {strategy_key}"),
                )
            ]
        )

    template = STRATEGY_PROMPTS[strategy_key]["template"]
    symbol = args.get("symbol", "AAPL")
    market = args.get("market", "US")

    filled_prompt = template.format(symbol=symbol, market=market)

    return GetPromptResult(
        description=f"{STRATEGY_PROMPTS[strategy_key]['name']} for {symbol}",
        messages=[
            PromptMessage(
                role="user",
                content=TextContent(type="text", text=filled_prompt),
            )
        ],
    )


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run the MCP server."""
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run())


if __name__ == "__main__":
    main()
