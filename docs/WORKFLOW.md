# Options Trader Platform - Workflow Guide

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Architecture Overview](#2-architecture-overview)
3. [Frontend Terminal (UI)](#3-frontend-terminal-ui)
4. [Analyze View (F1)](#4-analyze-view-f1)
5. [Dashboard View (F2)](#5-dashboard-view-f2)
6. [Trading View (F3)](#6-trading-view-f3)
7. [Risk View (F4)](#7-risk-view-f4)
8. [Decision Engine View (F5)](#8-decision-engine-view-f5)
9. [Data Providers](#9-data-providers)
10. [MCP Server (Claude Desktop)](#10-mcp-server-claude-desktop)
11. [API Reference](#11-api-reference)
12. [Daily Trading Workflow](#12-daily-trading-workflow)

---

## 1. Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Install & Run

```bash
# 1. Install Python backend
pip install -e .

# 2. Start the API server (port 8000)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Install frontend dependencies (first time only)
cd frontend && npm install

# 4. Start the frontend dev server (port 5173)
npx vite --host
```

### Access

| Service       | URL                        |
|---------------|----------------------------|
| Frontend UI   | http://localhost:5173      |
| API Docs      | http://localhost:8000/docs |
| Health Check  | http://localhost:8000/api/health |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (React)                    │
│         Bloomberg-style Terminal at :5173            │
│  ┌─────────┬──────────┬────────┬──────┬────────┐    │
│  │ Analyze │Dashboard │ Trade  │ Risk │ Engine │    │
│  │  (F1)   │  (F2)    │ (F3)   │ (F4) │ (F5)  │    │
│  └─────────┴──────────┴────────┴──────┴────────┘    │
└───────────────────────┬─────────────────────────────┘
                        │ HTTP/REST
┌───────────────────────┴─────────────────────────────┐
│              API SERVER (FastAPI) :8000              │
│  ┌─────────────────────────────────────────────┐    │
│  │         Decision Engine (GS/JPM)            │    │
│  │  Regime → Selector → Sizing → Rules         │    │
│  └─────────────────────────────────────────────┘    │
│  ┌────────────┐  ┌──────────┐  ┌───────────────┐   │
│  │  Providers  │  │ Services │  │ JPM Research  │   │
│  │ Mock/Yahoo/ │  │ Payoff,  │  │ Candidates,   │   │
│  │ IBKR/SAXO  │  │ Scanner  │  │ Screens       │   │
│  └────────────┘  └──────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────┘
                        │ stdio
┌───────────────────────┴─────────────────────────────┐
│           MCP SERVER (Claude Desktop)               │
│  19 Tools, 13 Resources, 12 Prompts                 │
└─────────────────────────────────────────────────────┘
```

---

## 3. Frontend Terminal (UI)

The UI is styled as a Bloomberg-terminal-like interface. All navigation is keyboard-driven.

### Keyboard Shortcuts

| Key        | Action                              |
|------------|-------------------------------------|
| `/`        | Open command bar                    |
| `?`        | Show keyboard shortcuts help        |
| `Esc`      | Close modals / cancel               |
| `Ctrl+,`   | Open settings                       |
| `F1`       | Analyze view                        |
| `F2`       | Dashboard view                      |
| `F3`       | Trading view                        |
| `F4`       | Risk view                           |
| `F5`       | Decision Engine view                |

### Command Bar

Press `/` to open the command bar. Type any of these commands:

| Command   | Destination                          |
|-----------|--------------------------------------|
| `AAPL`    | Analyze AAPL (overview)              |
| `AAPL OPT`| AAPL options chain                  |
| `AAPL VOL`| AAPL volatility surface             |
| `DASH`    | Dashboard                            |
| `TRADE`   | Trading page                         |
| `POS`     | Positions tab                        |
| `PAPER`   | Paper trading tab                    |
| `JRNL`    | Trade journal tab                    |
| `ALRT`    | Alerts tab                           |
| `SCAN`    | Options scanner                      |
| `CORR`    | Correlation matrix                   |
| `STRESS`  | Stress testing                       |
| `ENGINE`  | Decision Engine                      |
| `REGIME`  | Regime classification tab            |
| `REC`     | Strategy recommendations tab         |
| `TAIL`    | Tail risk panel                      |
| `JPM`     | JPM research tab                     |

### Header Bar

- **Provider Selector**: Switch between Mock, Yahoo, IBKR, SAXO data providers
- **Live Indicator**: Shows connection status
- **Clock**: Real-time clock
- **Status Bar** (bottom): Market hours for US, JP, HK

---

## 4. Analyze View (F1)

The primary view for researching individual symbols.

### Tabs

| Tab        | Content                                          |
|------------|--------------------------------------------------|
| Overview   | Quote, price chart, IV analysis, market sentiment |
| Options    | Full option chain (calls/puts), strike selector   |
| Volatility | 3D vol surface, IV term structure, skew analysis  |
| Strategy   | Payoff diagrams, probability calculator            |
| Research   | JPM research data, earnings calendar               |

### Workflow: Analyze a Symbol

1. Press `/`, type a symbol (e.g., `AAPL`), press Enter
2. **Overview tab**: Check price, IV rank, put/call ratio, unusual activity
3. **Options tab**: Browse the option chain, filter by expiration
4. **Volatility tab**: Review the IV surface, term structure, and skew for trade timing
5. **Strategy tab**: Build payoff diagrams with the strategy template selector
6. **Research tab**: Check JPM data for the stock (IV percentile, strategy candidates)

### Payoff Diagram Builder

- Select a strategy template (long call, bull call spread, iron condor, etc.)
- Adjust strikes and quantities
- View at-expiration and time-series payoff curves
- See max profit, max loss, breakeven points

### Probability Calculator

- Input current price, strike, DTE, and IV
- Outputs probability ITM/OTM, expected move, 1-sigma and 2-sigma ranges

---

## 5. Dashboard View (F2)

A market-wide overview panel.

### Sections

- **Watchlist**: Pre-seeded with 20 liquid names (SPY, QQQ, mega-cap tech, Asia). Add/remove symbols
- **Market Indicators**: Bonds (10Y yield, TLT), commodities (gold, oil, dollar), sector ETFs (XLF, XLK, etc.), market breadth
- **Fear/Greed Index**: CNN Fear & Greed data (or mock fallback) with 7 components
- **Unusual Activity**: High-volume/unusual options flow alerts

### Workflow: Morning Market Scan

1. Press `F2` to open Dashboard
2. Scan the Fear/Greed index for market sentiment
3. Check sector performance for rotation signals
4. Review bond yields and the yield curve spread
5. Look for unusual activity flags
6. Click any symbol in the watchlist to jump to its Analyze view

---

## 6. Trading View (F3)

Position management, paper trading, journaling, and alerts.

### Positions Tab (`POS`)

- View all open/closed positions with P&L
- Create new positions with multi-leg support
- Portfolio summary with aggregated Greeks (delta, gamma, theta, vega)
- Close or update individual positions

### Paper Trading Tab (`PAPER`)

- Virtual account with $100,000 starting balance
- Place market/limit orders for stocks and options
- Track paper positions and order history
- Reset account to start fresh

### Trade Journal Tab (`JRNL`)

- Log trades with entry price, strategy, tags
- Close trades with exit price, notes, and lessons learned
- View trading statistics: win rate, average P&L, profit factor
- Filter by strategy, symbol, or tags

### Alerts Tab (`ALRT`)

- Create alert rules: price above/below, IV above/below, volume spike
- Enable/disable individual rules
- View triggered notifications
- Acknowledge or dismiss alerts

---

## 7. Risk View (F4)

Portfolio risk analysis tools.

### Options Scanner (`SCAN`)

- **High IV Opportunities**: Stocks with rich implied volatility (premium selling candidates)
- **Low IV Opportunities**: Stocks with cheap volatility (buying candidates)
- **High Volume Activity**: Symbols with outsized options volume

### Correlation Matrix (`CORR`)

- Enter a comma-separated symbol list (default: SPY, QQQ, IWM, DIA)
- View pairwise correlation coefficients
- Identify diversification opportunities or concentration risk

### Stress Testing (`STRESS`)

- Predefined scenarios: Market Crash (-20%, +100% IV), Flash Crash, Mild Correction, Rally, Vol Spike, Vol Crush
- Custom scenario: specify price change % and IV change %
- See impact on each open position and total portfolio

---

## 8. Decision Engine View (F5)

The algorithmic decision engine based on Goldman Sachs and JPMorgan derivatives research (2003-2025). This is the core intelligence layer.

### Overview Tab

Shows the Regime Dashboard and Strategy Recommendations side by side.

### Regime Dashboard

The regime classifier uses a 6-priority system:

| Priority | Check             | Example Trigger                    |
|----------|-------------------|------------------------------------|
| 1        | Crisis Detection  | VIX > 30, HY OAS widening > 50bps |
| 2        | Liquidity Stress  | Bid-ask > 1.5x normal, depth < 60% |
| 3        | Event Window      | FOMC <= 5 days, CPI <= 3 days      |
| 4        | Vol Level         | VIX buckets: <12 to >30            |
| 5        | Trend             | SPX vs 50/200 SMA, breadth         |
| 6        | VVIX Instability  | VVIX > 22                          |

**Output**: Regime (VERY_LOW / LOW / NORMAL / ELEVATED / HIGH / EXTREME / CRISIS / LIQUIDITY_STRESS), Trend, Confidence (HIGH/MEDIUM/LOW), Event state, and action items.

**Color coding**: Green (VERY_LOW/LOW), Blue (NORMAL), Yellow (ELEVATED), Red (HIGH+).

### Strategy Recommendations Tab

1. **Set Objective**: Choose from Income, Directional, Hedging, Event, Relative Value, Tail, or All
2. **Set NAV**: Enter your portfolio net asset value
3. **Click Recommend**: The engine runs the full selector pipeline

The selector runs each of the 19 strategy templates through:

- **7 Entry Gates**: IV rank, event avoidance, liquidity, theta/gamma, regime compatibility, VVIX stability, strategy-specific
- **6-Dimension Scoring**: Edge (25%), Carry Fit (20%), Tail Risk (20%), Robustness (15%), Liquidity (10%), Complexity (10%)
- **Parameterization**: Delta adjusted by regime, DTE extended past events, size multiplied by regime/VVIX/confidence

Returns top 3 candidates with scores, parameters (delta, DTE, profit target, stop loss, roll DTE), and gate check details.

**Recommendation types**:
- `TRADE` - Full conviction, execute at recommended size
- `TRADE_CAUTIOUS` - Low confidence regime, defined-risk only, 50% size
- `LOW_CONVICTION` - Score < 5.0, reduce size or wait
- `NO_TRADE` - No strategy passes filters
- `REGIME_UNCERTAIN` - Mixed signals, wait

### Position Health Tab

Evaluate any open position against 16 rules:

**Adjustment Rules (A1-A9)**:

| Rule | Trigger                              | Action                                    |
|------|--------------------------------------|-------------------------------------------|
| A1   | DTE <= 21 for 30+ DTE strategies     | Roll to next monthly cycle                |
| A2   | DTE <= 7 for weeklies                | Close or let expire                       |
| A3   | Delta > 2x initial                   | Roll strikes, reduce size                 |
| A4   | Strangle tested (one side breached)  | Roll untested side closer                 |
| A5   | Portfolio delta > 20% of NAV         | Add delta-neutral hedge                   |
| A6   | VIX spikes > 5pts in 1 day           | Close naked, roll defined-risk wider      |
| A7   | Earnings < 5 days on underlier       | Close or roll past event                  |
| A8   | Regime changes between analyses      | Re-evaluate all positions                 |
| A9   | Implied correlation > 80th pctile    | Close dispersion trades                   |

**Exit Rules (X1-X7)**:

| Rule | Trigger                              | Action                                    |
|------|--------------------------------------|-------------------------------------------|
| X1   | Credit trade at 50% of max profit    | Close and redeploy                        |
| X2   | Debit trade at 100% of premium paid  | Close                                     |
| X3   | Credit trade loss > 2x premium       | Close immediately                         |
| X4   | Debit trade loss > 50% of premium    | Close                                     |
| X5   | 0DTE not profitable by 2:30 PM ET   | Close                                     |
| X6   | Regime exits strategy's allowed list | Close immediately                         |
| X7   | Daily portfolio loss > 1.5% of NAV  | Halt all new trades                       |

### Tail Risk Tab

**Hedge Allocation** (2% annual budget):
- VIX Call Spreads: 60% (buy spot+4, sell spot+12, 30-60 DTE)
- SPX Put Spreads: 25% (buy 5% OTM, sell 15% OTM, 90 DTE)
- Scheduled OTM Puts: 15% (monthly 5-10 delta puts)

**Early Warning Signals** (traffic lights):
- HY OAS widening > 50bps in 20 days
- Bid-ask spreads > 50% above 20d MA for 10+ days
- Implied correlation > 80th percentile in 5 days
- VVIX > 28 sustained 3+ days

**Crisis Protocol** (triggers: VIX > 35 OR 3+ warnings):
1. Close ALL naked short vol
2. Reduce defined-risk short vol by 75%
3. Deploy remaining hedge budget into convexity
4. Cash to 40%+ of NAV
5. Monitor for VIX peak (avg 2-4 weeks)
6. Do NOT sell vol until VIX downtrend established

**3-Pillar Tail Trading** (signal: term structure inversion, ts_1m_3m < 0):
- Delta Pillar: Long SPX 1M call spread (spot recovery)
- Gamma Pillar: Long SPX 5D 25-delta calls, daily hedge (62.2% hit rate)
- Vega Pillar: Long VIX put ladder (VIX mean reversion)

### Playbooks Tab

Event-specific trading playbooks with 3 phases each:

**FOMC Playbook**:
- Pre-Event (T-5 to T-1): Close naked short vol, reduce defined-risk 50%
- Event Eve (T-0): If trading, use iron condor 1.5x expected move, 25% size
- Post-Event (T+1 to T+3): Re-enter premium selling if VIX drops, full size

**Earnings Playbook**:
- Pre-Event (T-5 to T-1): Close or roll positions past event, calendar spreads
- Event Eve (T-0): Iron condor at 1.5x expected move or do nothing
- Post-Event (T+1 to T+3): Sell IV crush with strangles, aggressive premium selling

**0DTE Playbook** (day-of-week premiums):
- Monday: Low premium (0.3x), high risk - skip or small size
- Tuesday: Average premium (0.8x) - normal size
- Wednesday: Good premium (1.2x), FOMC days extra - preferred day
- Thursday: Best premium (1.5x), end-of-week flows - most favorable
- Friday: High premium (1.0x), fast decay - close by 2:30 PM

### Reference Tables Tab

8 backtested performance datasets from GS/JPM research:

| Table              | Content                                              |
|--------------------|------------------------------------------------------|
| put_selling        | GS 10yr put selling by delta (10-50)                 |
| overwriting        | GS 16yr covered call by delta (25-50)                |
| hedging            | GS 27yr hedge instrument comparison                  |
| sector_sensitivity | GS 15yr sector response to VIX spikes               |
| global_vol         | Cross-market vol levels (US, EU, Japan, EM)          |
| zero_dte_premium   | JPM 0DTE vol premium by day of week                  |
| vol_risk_premium   | GS/JPM vol risk premium by regime                    |
| tail_trading       | JPM 3-pillar tail trading backtest results           |

### Signal Conflict Resolution

The engine detects 8 conflict scenarios:

| Conflict | Signals                                  | Resolution                           |
|----------|------------------------------------------|--------------------------------------|
| C1       | High IV rank + High VVIX                 | Defined-risk only, no naked          |
| C2       | Bullish trend + Elevated vol regime      | Reduce short premium, add hedges     |
| C3       | Low IV rank + Event window               | Wait for post-event IV crush         |
| C4       | High IV + Term structure backwardation   | Short front-month, long back-month   |
| C5       | Bearish trend + Low vol                  | Buy puts (cheap), avoid selling      |
| C6       | Multiple events in 5-day window          | Flat or minimal positions only       |
| C7       | Tail signal active + Short premium on    | Close short premium immediately      |
| C8       | High IV rank + Falling realized vol      | Sell premium with tight stops        |

A yellow/orange banner appears at the top of the Engine page when conflicts are detected.

---

## 9. Data Providers

### Mock (Default)

Generates synthetic market data. No external dependencies. Used for development and testing.

### Yahoo Finance

Free real-time data via `yfinance`. Switch to it in the header dropdown or via:
```
POST /api/providers/switch  {"provider": "yahoo"}
```

Supports US equities. Rate-limited to 2 seconds between requests.

### Interactive Brokers (IBKR)

Requires TWS or IB Gateway running locally.

```
POST /api/providers/switch  {
  "provider": "ibkr",
  "host": "127.0.0.1",
  "port": 7497,       // 7497=paper, 7496=live
  "client_id": 1
}
```

### SAXO OpenAPI

Requires OAuth2 access token from Saxo Developer Portal.

```
POST /api/providers/switch  {
  "provider": "saxo",
  "access_token": "your-token",
  "environment": "sim"   // sim or live
}
```

---

## 10. MCP Server (Claude Desktop)

The platform runs as an MCP server for integration with Claude Desktop.

### Setup

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "options-trader": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:/Working/Claude_Projects/OptionsTrader"
    }
  }
}
```

### Available Tools (19)

**Market Data**:
- `get_quote` - Real-time price quote
- `get_option_chain` - Options chain (calls/puts)
- `get_volatility_surface` - IV surface across strikes/expirations
- `add_to_watchlist` / `remove_from_watchlist`
- `list_providers` / `switch_provider`

**JPM Research**:
- `get_jpm_trading_candidates` - Strategy candidates by type
- `get_jpm_volatility_screen` - IV screen results
- `get_jpm_stock_data` - Single stock research data
- `get_jpm_summary` - Full research overview
- `search_jpm_stocks` - Filter by IV, sector, etc.

**Decision Engine**:
- `get_market_regime` - Classify current regime
- `get_strategy_recommendations` - Top-3 strategy picks (args: nav, objective)
- `run_full_analysis` - Complete pipeline (regime + strategies + tail risk + conflicts)
- `evaluate_position_health` - Check position against rules A1-A9, X1-X7
- `get_tail_risk_assessment` - Hedge allocation, warnings, crisis protocol
- `get_event_playbook` - Event-specific playbook (FOMC, Earnings, CPI, NFP, 0DTE)
- `get_reference_table` - Backtested performance data (8 tables)
- `resolve_conflict` - Check for conflicting signals

### Available Resources (13)

- `markets://all`, `markets://us`, `markets://jp`, `markets://hk`
- `watchlist://default`
- `jpm://summary`, `jpm://call-overwriting`, `jpm://call-buying`, `jpm://put-underwriting`, `jpm://put-buying`, `jpm://rich-iv`, `jpm://cheap-iv`, `jpm://iv-movers`
- `engine://regime`, `engine://strategies`, `engine://tail-risk`, `engine://reference-tables`

### Available Prompts (12)

**Strategy Prompts** (require symbol + market):
- `strategy-bullish`, `strategy-bearish`, `strategy-neutral`, `strategy-volatile`

**JPM Prompts**:
- `jpm-income`, `jpm-directional`, `jpm-volatility`, `jpm-stock-analysis`, `jpm-portfolio`

**Engine Prompts**:
- `engine-analysis` - Full decision engine briefing
- `engine-position-review` - Position health check against all rules
- `engine-event-preparation` - Event playbook with preparation steps

### Example MCP Conversations

**Morning briefing**:
> "Run a full engine analysis for my $50,000 portfolio focused on income strategies"

Uses: `run_full_analysis(nav=50000, objective="income")`

**Position check**:
> "I have a cash-secured put with 15 DTE, check if I need to adjust"

Uses: `evaluate_position_health(strategy="cash_secured_put", dte=15, family="short_premium")`

**Event prep**:
> "FOMC is in 3 days, what should I do?"

Uses: `get_event_playbook(event_type="FOMC")` + `get_market_regime()`

---

## 11. API Reference

### Base URL: `http://localhost:8000/api`

### Core Endpoints

| Method | Path                              | Description                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/health`                         | Health check                   |
| GET    | `/markets`                        | Supported markets info         |
| GET    | `/providers`                      | List data providers            |
| POST   | `/providers/switch`               | Switch active provider         |

### Market Data

| Method | Path                              | Description                    |
|--------|-----------------------------------|--------------------------------|
| GET    | `/quote/{symbol}`                 | Real-time quote                |
| GET    | `/options/{symbol}`               | Option chain                   |
| GET    | `/volatility/{symbol}`            | Vol surface                    |
| GET    | `/history/{symbol}`               | Price history                  |
| GET    | `/iv-analysis/{symbol}`           | IV rank/percentile             |
| GET    | `/iv-history/{symbol}`            | Historical IV data             |
| GET    | `/term-structure/{symbol}`        | IV term structure              |
| GET    | `/skew/{symbol}`                  | Strike skew analysis           |
| GET    | `/market-sentiment/{symbol}`      | Put/call ratio, sentiment      |
| GET    | `/unusual-activity`               | Unusual options flow           |
| GET    | `/strategy-suggestions/{symbol}`  | Strategy suggestions           |
| GET    | `/earnings`                       | Earnings calendar              |
| GET    | `/correlation`                    | Correlation matrix             |
| GET    | `/fear-greed`                     | CNN Fear & Greed Index         |
| GET    | `/market-indicators`              | Bonds, commodities, sectors    |

### Watchlist

| Method | Path                     | Description            |
|--------|--------------------------|------------------------|
| GET    | `/watchlist`             | Get watchlist          |
| POST   | `/watchlist`             | Add to watchlist       |
| DELETE | `/watchlist/{symbol}`    | Remove from watchlist  |

### Payoff Calculator

| Method | Path                          | Description              |
|--------|-------------------------------|--------------------------|
| POST   | `/payoff/calculate`           | Calculate payoff diagram |
| POST   | `/payoff/time-series`         | Theta decay visualization|
| GET    | `/payoff/templates/{strategy}`| Strategy leg templates   |
| GET    | `/payoff/strategies`          | List strategy templates  |

### Positions & Trading

| Method | Path                            | Description              |
|--------|---------------------------------|--------------------------|
| GET    | `/positions`                    | All positions            |
| GET    | `/positions/open`               | Open positions only      |
| GET    | `/positions/summary`            | Portfolio summary        |
| POST   | `/positions`                    | Create position          |
| PUT    | `/positions/{id}`               | Update position          |
| POST   | `/positions/{id}/close`         | Close position           |
| DELETE | `/positions/{id}`               | Delete position          |

### Paper Trading

| Method | Path                             | Description             |
|--------|----------------------------------|-------------------------|
| GET    | `/paper/accounts`                | List accounts           |
| POST   | `/paper/accounts`                | Create account          |
| GET    | `/paper/accounts/default`        | Get default account     |
| GET    | `/paper/accounts/{id}`           | Get account by ID       |
| POST   | `/paper/accounts/{id}/reset`     | Reset account           |
| POST   | `/paper/orders`                  | Place order             |
| GET    | `/paper/orders`                  | List orders             |
| DELETE | `/paper/orders/{id}`             | Cancel order            |
| GET    | `/paper/positions`               | List paper positions    |

### Trade Journal

| Method | Path                          | Description             |
|--------|-------------------------------|-------------------------|
| GET    | `/journal/trades`             | All trades              |
| GET    | `/journal/trades/open`        | Open trades             |
| GET    | `/journal/stats`              | Trading statistics      |
| POST   | `/journal/trades`             | Log new trade           |
| POST   | `/journal/trades/{id}/close`  | Close trade             |
| PUT    | `/journal/trades/{id}`        | Update trade            |
| DELETE | `/journal/trades/{id}`        | Delete trade            |

### Alerts

| Method | Path                                      | Description           |
|--------|-------------------------------------------|-----------------------|
| GET    | `/alerts/rules`                           | All alert rules       |
| POST   | `/alerts/rules`                           | Create rule           |
| PUT    | `/alerts/rules/{id}`                      | Update rule           |
| POST   | `/alerts/rules/{id}/toggle`               | Toggle enabled        |
| DELETE | `/alerts/rules/{id}`                      | Delete rule           |
| GET    | `/alerts/notifications`                   | All notifications     |
| GET    | `/alerts/notifications/unread`            | Unread notifications  |
| POST   | `/alerts/notifications/{id}/acknowledge`  | Acknowledge           |
| POST   | `/alerts/notifications/acknowledge-all`   | Acknowledge all       |

### Options Scanner

| Method | Path                   | Description             |
|--------|------------------------|-------------------------|
| POST   | `/scanner/scan`        | Custom scan criteria    |
| GET    | `/scanner/high-iv`     | High IV opportunities   |
| GET    | `/scanner/low-iv`      | Low IV opportunities    |
| GET    | `/scanner/high-volume` | High volume activity    |

### Stress Testing

| Method | Path                      | Description             |
|--------|---------------------------|-------------------------|
| POST   | `/stress-test`            | Run stress test         |
| GET    | `/stress-test/scenarios`  | Predefined scenarios    |

### JPM Research

| Method | Path                       | Description                |
|--------|----------------------------|----------------------------|
| GET    | `/jpm/report`              | Research report metadata   |
| GET    | `/jpm/trading-candidates`  | Strategy candidates        |
| GET    | `/jpm/volatility-screen`   | IV screen results          |
| GET    | `/jpm/stocks`              | All stocks (filterable)    |
| GET    | `/jpm/stock/{ticker}`      | Single stock data          |
| GET    | `/jpm/full`                | Complete research data     |

### Decision Engine

| Method | Path                             | Description                      |
|--------|----------------------------------|----------------------------------|
| GET    | `/engine/regime`                 | Current regime classification    |
| GET    | `/engine/regime/history`         | Regime history                   |
| POST   | `/engine/recommend`              | Strategy recommendations         |
| POST   | `/engine/analysis`               | Full decision pipeline           |
| GET    | `/engine/strategies`             | Strategy universe catalog        |
| GET    | `/engine/strategies/{family}`    | Strategies by family             |
| GET    | `/engine/tail-risk`              | Tail risk assessment             |
| GET    | `/engine/early-warnings`         | Active early warning signals     |
| GET    | `/engine/conflicts`              | All conflicts with status        |
| GET    | `/engine/conflicts/active`       | Only detected conflicts          |
| POST   | `/engine/positions/evaluate`     | Evaluate position health         |
| GET    | `/engine/playbook/{event_type}`  | Event playbook                   |
| GET    | `/engine/playbook/0dte/info`     | 0DTE playbook                    |
| GET    | `/engine/playbook/0dte/{day}`    | 0DTE day recommendation          |
| GET    | `/engine/reference`              | List reference tables            |
| GET    | `/engine/reference/{table_name}` | Get reference table data         |
| POST   | `/engine/review`                 | Create post-trade review         |

---

## 12. Daily Trading Workflow

### Pre-Market (Before 9:30 AM ET)

1. **Open the terminal**: http://localhost:5173
2. **Check regime** (`F5` or `/REGIME`): Note the current regime, confidence, and actions
3. **Review tail risk** (`/TAIL`): Check early warning signals and hedge status
4. **Scan dashboard** (`F2`): Fear/Greed, sector rotation, bond yields
5. **Check conflicts**: Look at the conflict banner on the Engine page
6. **Run full analysis**: On Engine > Overview, review recommendations for your NAV/objective

### During Market Hours

7. **Execute recommendations**: Open trades based on engine's top picks with specified parameters
8. **Log positions**: Record in Trading > Positions with strategy name and legs
9. **Monitor positions**: Use Position Health tab to check against adjustment/exit rules
10. **Watch for events**: If in an event window, follow the appropriate playbook

### Post-Market

11. **Review P&L**: Check positions for triggered exit rules (X1-X7)
12. **Journal trades**: Log closed trades with lessons learned
13. **Prepare for tomorrow**: Check earnings calendar, upcoming events
14. **Re-run analysis**: Get fresh regime reading for overnight positioning

### Weekly Review

- Run stress tests on open positions (Risk > Stress)
- Review trade journal statistics
- Check if hedge allocation needs rebalancing
- Compare realized vs expected performance using reference tables
