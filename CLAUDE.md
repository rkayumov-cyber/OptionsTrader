# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cross-Market Equities Options Strategy Platform - an MCP server providing real-time options data and strategy recommendations for US, Japan, and HKEX equities markets.

## Build & Run Commands

```bash
# Install dependencies
pip install -e .

# Run MCP server (stdio mode)
python -m mcp_server.server

# Run tests
pytest

# Type checking (if added)
mypy mcp_server
```

## Architecture

### MCP Server (`mcp_server/`)
- `server.py` - Main entry point, registers all tools/resources/prompts
- `models.py` - Pydantic data models (Quote, OptionChain, VolatilitySurface, Greeks)
- `providers/` - Market data provider implementations
  - `base.py` - Abstract `MarketDataProvider` interface
  - `mock.py` - Simulated data for testing
  - `yahoo.py` - Yahoo Finance via `yfinance`
  - (Planned: `ibkr.py`, `saxo.py`)

### MCP Capabilities
**Tools:**
- `get_quote` - Real-time price for symbol
- `get_option_chain` - Options with strikes/expirations/IV
- `get_volatility_surface` - IV grid across strikes and tenors
- `add_to_watchlist` / `remove_from_watchlist`

**Resources:**
- `markets://us`, `markets://jp`, `markets://hk` - Market info
- `watchlist://default` - User's tracked symbols

**Prompts:**
- `strategy-bullish`, `strategy-bearish`, `strategy-neutral`, `strategy-volatile`

### Provider Pattern
All providers implement `MarketDataProvider` ABC with async methods:
- `get_quote(symbol, market) -> Quote`
- `get_option_chain(symbol, market, expiration?) -> OptionChain`
- `get_volatility_surface(symbol, market) -> VolatilitySurface`

### Configuration
`config/providers.yaml` - Provider settings (API keys, endpoints)

## Claude Desktop Integration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "options-trader": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/OptionsTrader"
    }
  }
}
```
