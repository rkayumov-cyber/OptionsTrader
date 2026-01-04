"""Test script for MCP server with Yahoo Finance provider."""

import asyncio
import json


async def test_yahoo():
    """Test server tools with Yahoo Finance provider."""
    from mcp_server.server import call_tool, list_tools, get_provider, switch_provider

    print("=" * 60)
    print("OPTIONS TRADER MCP SERVER - YAHOO FINANCE TEST")
    print("=" * 60)

    # Switch to Yahoo provider
    print("\nSwitching to Yahoo Finance provider...")
    success, message = switch_provider("yahoo")
    print(f"Result: {message}")

    provider = get_provider()
    print(f"Active Provider: {provider.name}")

    # Test get_quote - US Market
    print("\n" + "-" * 40)
    print("TEST: get_quote (AAPL, US)")
    print("-" * 40)
    try:
        result = await call_tool("get_quote", {"symbol": "AAPL", "market": "US"})
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # Test get_quote - Another US stock
    print("\n" + "-" * 40)
    print("TEST: get_quote (MSFT, US)")
    print("-" * 40)
    try:
        result = await call_tool("get_quote", {"symbol": "MSFT", "market": "US"})
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # Test get_quote - JP Market
    print("\n" + "-" * 40)
    print("TEST: get_quote (7203, JP) - Toyota")
    print("-" * 40)
    try:
        result = await call_tool("get_quote", {"symbol": "7203", "market": "JP"})
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # Test get_quote - HK Market
    print("\n" + "-" * 40)
    print("TEST: get_quote (0700, HK) - Tencent")
    print("-" * 40)
    try:
        result = await call_tool("get_quote", {"symbol": "0700", "market": "HK"})
        print(result[0].text)
    except Exception as e:
        print(f"Error: {e}")

    # Test get_option_chain - US (only US has good options data on Yahoo)
    print("\n" + "-" * 40)
    print("TEST: get_option_chain (AAPL, US)")
    print("-" * 40)
    try:
        result = await call_tool("get_option_chain", {"symbol": "AAPL", "market": "US"})
        data = json.loads(result[0].text)
        print(f"Underlying: {data['underlying']}")
        print(f"Market: {data['market']}")
        print(f"Expirations: {data['expirations'][:5]}...")  # First 5
        print(f"Total Calls: {data['num_calls']}")
        print(f"Total Puts: {data['num_puts']}")
        if data['calls_sample']:
            print(f"\nSample Call Option:")
            sample = data['calls_sample'][0]
            print(f"  Symbol: {sample['symbol']}")
            print(f"  Strike: ${sample['strike']}")
            print(f"  Expiration: {sample['expiration']}")
            print(f"  Bid/Ask: ${sample['bid']} / ${sample['ask']}")
            print(f"  IV: {sample['implied_volatility']}")
    except Exception as e:
        print(f"Error: {e}")

    # Test get_option_chain with specific expiration
    print("\n" + "-" * 40)
    print("TEST: get_option_chain (SPY, US) - ETF")
    print("-" * 40)
    try:
        result = await call_tool("get_option_chain", {"symbol": "SPY", "market": "US"})
        data = json.loads(result[0].text)
        print(f"Underlying: {data['underlying']}")
        print(f"Expirations available: {len(data['expirations'])}")
        print(f"Total Calls: {data['num_calls']}")
        print(f"Total Puts: {data['num_puts']}")
    except Exception as e:
        print(f"Error: {e}")

    # Test get_volatility_surface
    print("\n" + "-" * 40)
    print("TEST: get_volatility_surface (AAPL, US)")
    print("-" * 40)
    try:
        result = await call_tool("get_volatility_surface", {"symbol": "AAPL", "market": "US"})
        data = json.loads(result[0].text)
        print(f"Symbol: {data['symbol']}")
        print(f"Market: {data['market']}")
        print(f"Strikes: {len(data['strikes'])} strikes from ${min(data['strikes']):.2f} to ${max(data['strikes']):.2f}")
        print(f"Expirations: {len(data['expirations'])}")
        if data['call_ivs'] and data['call_ivs'][0]:
            # Find non-zero IVs
            sample_ivs = [iv for row in data['call_ivs'] for iv in row if iv > 0]
            if sample_ivs:
                print(f"Call IV range: {min(sample_ivs):.2%} to {max(sample_ivs):.2%}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("YAHOO FINANCE TEST COMPLETED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_yahoo())
