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

    return json.dumps({"error": f"Unknown resource: {uri}"})


# =============================================================================
# PROMPTS
# =============================================================================

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
    return [
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
        for key, info in STRATEGY_PROMPTS.items()
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> GetPromptResult:
    """Get a prompt with arguments filled in."""
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
    args = arguments or {}
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
