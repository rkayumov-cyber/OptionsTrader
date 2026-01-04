"""Test script for MCP server with mock provider."""

import asyncio
import json


async def test_server():
    """Test server tools with mock provider."""
    from mcp_server.server import call_tool, list_tools, get_provider, active_provider_name

    print("=" * 60)
    print("OPTIONS TRADER MCP SERVER TEST")
    print("=" * 60)

    # Check active provider
    provider = get_provider()
    print(f"\nActive Provider: {provider.name}")
    print(f"Supported Markets: {provider.supported_markets}")

    # List available tools
    print("\n" + "-" * 40)
    print("AVAILABLE TOOLS:")
    print("-" * 40)
    tools = await list_tools()
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")

    # Test get_quote
    print("\n" + "-" * 40)
    print("TEST: get_quote (AAPL, US)")
    print("-" * 40)
    result = await call_tool("get_quote", {"symbol": "AAPL", "market": "US"})
    print(result[0].text)

    # Test get_quote for JP market
    print("\n" + "-" * 40)
    print("TEST: get_quote (7203.T, JP) - Toyota")
    print("-" * 40)
    result = await call_tool("get_quote", {"symbol": "7203.T", "market": "JP"})
    print(result[0].text)

    # Test get_quote for HK market
    print("\n" + "-" * 40)
    print("TEST: get_quote (0700.HK, HK) - Tencent")
    print("-" * 40)
    result = await call_tool("get_quote", {"symbol": "0700.HK", "market": "HK"})
    print(result[0].text)

    # Test get_option_chain
    print("\n" + "-" * 40)
    print("TEST: get_option_chain (AAPL, US)")
    print("-" * 40)
    result = await call_tool("get_option_chain", {"symbol": "AAPL", "market": "US"})
    print(result[0].text)

    # Test get_volatility_surface
    print("\n" + "-" * 40)
    print("TEST: get_volatility_surface (AAPL, US)")
    print("-" * 40)
    result = await call_tool("get_volatility_surface", {"symbol": "AAPL", "market": "US"})
    data = json.loads(result[0].text)
    print(f"Symbol: {data['symbol']}")
    print(f"Market: {data['market']}")
    print(f"Strikes: {data['strikes']}")
    print(f"Expirations: {data['expirations']}")
    print(f"Call IV grid shape: {len(data['call_ivs'])}x{len(data['call_ivs'][0]) if data['call_ivs'] else 0}")

    # Test list_providers
    print("\n" + "-" * 40)
    print("TEST: list_providers")
    print("-" * 40)
    result = await call_tool("list_providers", {})
    print(result[0].text)

    # Test watchlist operations
    print("\n" + "-" * 40)
    print("TEST: add_to_watchlist")
    print("-" * 40)
    result = await call_tool("add_to_watchlist", {"symbol": "NVDA", "market": "US", "name": "NVIDIA"})
    print(result[0].text)
    result = await call_tool("add_to_watchlist", {"symbol": "7203.T", "market": "JP", "name": "Toyota"})
    print(result[0].text)

    # Read watchlist resource
    print("\n" + "-" * 40)
    print("TEST: read watchlist resource")
    print("-" * 40)
    from mcp_server.server import read_resource
    watchlist_data = await read_resource("watchlist://default")
    print(watchlist_data)

    # Test remove from watchlist
    print("\n" + "-" * 40)
    print("TEST: remove_from_watchlist")
    print("-" * 40)
    result = await call_tool("remove_from_watchlist", {"symbol": "NVDA", "market": "US"})
    print(result[0].text)

    # Read market resources
    print("\n" + "-" * 40)
    print("TEST: read markets resource")
    print("-" * 40)
    markets_data = await read_resource("markets://all")
    print(markets_data)

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_server())
