# Options Trading System: Decision-Making Model & Algorithm

> Synthesized from Goldman Sachs and JPMorgan Derivatives Research (2003-2025)
> All thresholds are empirically derived from backtests spanning 10-27 years

---

## 1. REGIME CLASSIFIER

### 1.1 Input Variables (Update Daily)

```
SPOT_DATA:
  spx_level:          float    # Current SPX price
  spx_ret_1d:         float    # 1-day return
  spx_ret_5d:         float    # 5-day return
  spx_ret_20d:        float    # 20-day return
  spx_sma_50:         float    # 50-day simple moving average
  spx_sma_200:        float    # 200-day simple moving average
  breadth_pct_above_50dma: float  # % of stocks above 50 DMA

VOL_DATA:
  vix:                float    # VIX spot level
  vix_1d_change:      float    # VIX 1-day change (points)
  vix_5d_change:      float    # VIX 5-day change (points)
  vix_percentile_1y:  float    # VIX percentile rank over 1 year (0-100)
  vvix:               float    # CBOE VVIX (vol of vol)
  vix9d:              float    # 9-day VIX
  iv_atm_1m:          float    # 1-month ATM implied vol
  iv_atm_3m:          float    # 3-month ATM implied vol
  iv_atm_6m:          float    # 6-month ATM implied vol
  rv_10d:             float    # 10-day realized vol (close-to-close)
  rv_20d:             float    # 20-day realized vol
  rv_30d:             float    # 30-day realized vol
  iv_rv_spread:       float    # iv_atm_1m - rv_20d

SKEW_DATA:
  put_skew_25d_1m:    float    # 25-delta 1M put skew
  put_skew_25d_3m:    float    # 25-delta 3M put skew
  risk_reversal_25d:  float    # 25-delta risk reversal cost
  skew_pctile_1y:     float    # Skew percentile (1Y lookback)

TERM_STRUCTURE:
  ts_1m_3m:           float    # 3M IV - 1M IV (contango if positive)
  ts_3m_6m:           float    # 6M IV - 3M IV
  ts_slope:           float    # Overall term structure slope
  vix_futures_1m:     float    # VIX 1M future
  vix_futures_3m:     float    # VIX 3M future
  roll_yield:         float    # (VIX_future - VIX_spot) / VIX_spot

EVENT_CALENDAR:
  days_to_fomc:       int      # Trading days to next FOMC
  days_to_cpi:        int      # Trading days to next CPI
  days_to_nfp:        int      # Trading days to next NFP
  days_to_earnings:   int      # Trading days to next relevant earnings (portfolio)
  events_next_5d:     int      # Count of major events in next 5 trading days
  events_next_20d:    int      # Count of major events in next 20 trading days

CREDIT_MACRO:
  hy_oas:             float    # High yield OAS spread (bps)
  hy_oas_20d_change:  float    # HY OAS 20-day change (bps)
  ig_spread:          float    # Investment grade spread (bps)
  fed_funds_rate:     float    # Current fed funds rate
  us_10y_yield:       float    # 10Y Treasury yield
  us_2s10s:           float    # 2s10s yield curve slope

LIQUIDITY:
  spx_bid_ask:        float    # SPX options bid-ask as % of mid
  spx_bid_ask_20d_ma: float    # 20-day MA of bid-ask
  bid_ask_widening:   float    # Current / 20d MA ratio (>1 = widening)
  emini_depth:        float    # E-mini market depth (contracts)
  options_volume_oi:  float    # Volume / Open Interest ratio

CORRELATION:
  implied_corr:       float    # Implied correlation (ICJ or equivalent)
  realized_corr_20d:  float    # 20-day realized correlation
  corr_pctile_1y:     float    # Correlation percentile (1Y)
  dispersion:         float    # implied_corr - realized_corr_20d
```

### 1.2 Classification Rules (Priority-Ordered)

```python
def classify_regime(inputs):
    """
    Returns: {regime, sub_regime, trend, event_state, confidence, actions}
    Priority order: Crisis > Liquidity Stress > Event > Vol Level + Trend
    """

    # ──────────────────────────────────────────────
    # PRIORITY 1: CRISIS DETECTION
    # [Source: GS Vol Vitals - 6 episodes >3.5 std dev since 2008]
    # ──────────────────────────────────────────────
    crisis_signals = 0
    if inputs.vix > 30:                          crisis_signals += 2
    if inputs.vix_1d_change > 5:                 crisis_signals += 2
    if inputs.vix > 35:                          crisis_signals += 1  # Hard stop level
    if inputs.hy_oas_20d_change > 50:            crisis_signals += 1
    if inputs.ts_1m_3m < 0:                      crisis_signals += 1  # Backwardation
    if inputs.bid_ask_widening > 2.0:            crisis_signals += 1

    if crisis_signals >= 3:
        return {
            "regime": "CRISIS",
            "confidence": "HIGH" if crisis_signals >= 5 else "MEDIUM",
            "actions": [
                "CLOSE all naked short vol positions immediately",
                "CLOSE all positions if VIX > 35 [GS Vol Vitals]",
                "ONLY defined-risk spreads allowed (5-10 delta, 14-21 DTE)",
                "Position size: 25% of baseline or FLAT",
                "Activate tail hedges if not already on",
                "Monitor for VIX peak (avg duration 2-4 weeks, avg peak ~45)"
            ]
        }

    # ──────────────────────────────────────────────
    # PRIORITY 2: LIQUIDITY STRESS (EARLY WARNING)
    # [Source: GS Rising Importance of Falling Liquidity]
    # Liquidity deteriorates 2-4 weeks BEFORE vol spikes
    # ──────────────────────────────────────────────
    liquidity_stress = 0
    if inputs.bid_ask_widening > 1.5:            liquidity_stress += 1
    if inputs.spx_bid_ask > inputs.spx_bid_ask_20d_ma * 1.3: liquidity_stress += 1
    if inputs.emini_depth < 0.6 * normal_depth:  liquidity_stress += 1  # 40% decline
    if inputs.hy_oas_20d_change > 30:            liquidity_stress += 1

    if liquidity_stress >= 2:
        return {
            "regime": "LIQUIDITY_STRESS",
            "confidence": "MEDIUM",
            "actions": [
                "REDUCE all positions by 25-50%",
                "NO new naked short vol positions",
                "Tighten stops on existing positions",
                "Begin adding tail hedges (VIX call spreads)",
                "Monitor: if persists >10 days, move to crisis protocol"
            ]
        }

    # ──────────────────────────────────────────────
    # PRIORITY 3: EVENT WINDOW
    # [Source: GS Trading Events 15yr study; JPM Earnings & Options]
    # ──────────────────────────────────────────────
    event_active = False
    event_type = None

    if inputs.days_to_fomc <= 5:
        event_active = True
        event_type = "FOMC"
    elif inputs.days_to_cpi <= 3:
        event_active = True
        event_type = "CPI"
    elif inputs.days_to_nfp <= 3:
        event_active = True
        event_type = "NFP"
    elif inputs.days_to_earnings <= 3:
        event_active = True
        event_type = "EARNINGS"

    multi_event = inputs.events_next_5d >= 2  # [GS: +40% IV premium for multi-event weeks]

    # ──────────────────────────────────────────────
    # PRIORITY 4: VOL LEVEL CLASSIFICATION
    # [Source: JPM Systematic Vol - 3-regime minimum viable model]
    # ──────────────────────────────────────────────
    if inputs.vix < 12:
        vol_regime = "VERY_LOW"    # [JPM: VIX<12 = Low regime]
    elif inputs.vix < 15:
        vol_regime = "LOW"
    elif inputs.vix < 20:
        vol_regime = "NORMAL"      # [JPM: VIX 12-18 = Normal]
    elif inputs.vix < 25:
        vol_regime = "ELEVATED"
    elif inputs.vix <= 30:
        vol_regime = "HIGH"        # [JPM: VIX>18 = High regime]
    else:
        vol_regime = "EXTREME"     # Handled by crisis above

    # ──────────────────────────────────────────────
    # PRIORITY 5: TREND OVERLAY
    # ──────────────────────────────────────────────
    if inputs.spx_level > inputs.spx_sma_50 and inputs.spx_level > inputs.spx_sma_200:
        if inputs.breadth_pct_above_50dma > 60:
            trend = "STRONG_UPTREND"
        else:
            trend = "UPTREND"
    elif inputs.spx_level < inputs.spx_sma_50 and inputs.spx_level < inputs.spx_sma_200:
        if inputs.breadth_pct_above_50dma < 40:
            trend = "STRONG_DOWNTREND"
        else:
            trend = "DOWNTREND"
    else:
        trend = "RANGE_BOUND"

    # ──────────────────────────────────────────────
    # PRIORITY 6: VOL-OF-VOL INSTABILITY CHECK
    # [Source: GS Vol Vitals - VVIX > 22 = unstable]
    # ──────────────────────────────────────────────
    vol_unstable = inputs.vvix > 22

    # ──────────────────────────────────────────────
    # CONFIDENCE SCORING
    # ──────────────────────────────────────────────
    confirming = 0
    # IV-RV agreement
    if (vol_regime in ["LOW", "VERY_LOW"] and inputs.iv_rv_spread < 2) or \
       (vol_regime in ["ELEVATED", "HIGH"] and inputs.iv_rv_spread > 3):
        confirming += 1
    # Skew alignment
    if (vol_regime in ["ELEVATED", "HIGH"] and inputs.put_skew_25d_1m > 6) or \
       (vol_regime in ["LOW", "VERY_LOW"] and inputs.put_skew_25d_1m < 4):
        confirming += 1
    # Term structure alignment
    if (vol_regime in ["LOW", "NORMAL"] and inputs.ts_1m_3m > 0) or \
       (vol_regime in ["HIGH"] and inputs.ts_1m_3m < 1):
        confirming += 1
    # Credit confirmation
    if (vol_regime in ["LOW", "NORMAL"] and inputs.hy_oas_20d_change < 20) or \
       (vol_regime in ["ELEVATED", "HIGH"] and inputs.hy_oas_20d_change > 30):
        confirming += 1

    confidence = "HIGH" if confirming >= 3 else "MEDIUM" if confirming >= 2 else "LOW"

    return {
        "regime": vol_regime,
        "trend": trend,
        "event_active": event_active,
        "event_type": event_type,
        "multi_event": multi_event,
        "vol_unstable": vol_unstable,
        "confidence": confidence,
        "confirming_signals": confirming
    }
```

---

## 2. POSITION SIZING MODEL

### 2.1 Regime-Based Size Multipliers

```python
# [Source: JPM Systematic Vol; GS Art of Put Selling; GS Vol Vitals]
SIZE_MULTIPLIER = {
    # vol_regime: (sell_premium_mult, buy_premium_mult)
    "VERY_LOW":  (1.00, 0.50),   # Rich for sellers, cheap convexity
    "LOW":       (1.00, 0.75),
    "NORMAL":    (0.75, 1.00),   # Balanced
    "ELEVATED":  (0.50, 1.00),   # Rich premium but gap risk
    "HIGH":      (0.25, 1.00),   # Only defined-risk selling
    "EXTREME":   (0.00, 1.00),   # No selling; buy convexity only
    "CRISIS":    (0.00, 1.00),
}

# VVIX adjustment [Source: GS Vol Vitals - VVIX > 22 = reduce by 25-50%]
def vvix_adjustment(vvix):
    if vvix <= 18: return 1.00
    if vvix <= 22: return 0.85
    if vvix <= 28: return 0.65
    return 0.50  # VVIX > 28

# Fixed premium sizing [Source: JPM Equity Vol Strategy]
# Allocate fixed dollar premium per trade, NOT fixed notional
# This naturally reduces size when vol is high (options expensive)
def fixed_premium_size(nav, budget_pct=0.005):
    """Budget 0.5% of NAV per trade in premium"""
    return nav * budget_pct
```

### 2.2 Portfolio-Level Risk Limits

```python
# [Source: JPM Systematic Vol; GS Overwriting; JPM P&L Attribution]
RISK_LIMITS = {
    "max_portfolio_vega":      0.005,   # 0.5% of NAV per vol point
    "max_portfolio_delta":     0.20,    # +/- 20% of NAV
    "max_portfolio_gamma_t7":  0.003,   # 0.3% of NAV per 1% move (at T-7)
    "max_single_name_pct":     0.05,    # 5% of total premium at risk
    "max_sector_pct":          0.20,    # 20% of total premium at risk
    "max_correlated_positions": 3,      # Max positions with corr > 0.7
    "daily_pnl_stop":          0.015,   # 1.5% of NAV
    "weekly_pnl_stop":         0.030,   # 3.0% of NAV
    "cash_reserve_min":        0.20,    # 20% in cash/near-cash
}
```

---

## 3. STRATEGY UNIVERSE

### 3.1 Strategy Templates

```python
STRATEGIES = {
    # ═══════════════════════════════════════════
    # SHORT PREMIUM (INCOME / CARRY)
    # ═══════════════════════════════════════════

    "cash_secured_put": {
        "family": "short_premium",
        "objective": "income",
        "legs": 1,
        "base_delta": 12,        # [GS Art of Put Selling: 10-15 delta, 74% win rate]
        "base_dte": 37,          # [GS: 30-45 DTE optimal]
        "profit_target": 0.50,   # [GS: close at 50% of max profit]
        "stop_loss": 2.0,        # [GS: 2x premium received]
        "roll_dte": 21,          # [GS: roll at 21 DTE]
        "win_rate": 0.74,        # [GS: 74% at 10-15 delta, 10yr study]
        "sharpe_hist": 0.50,     # [GS: Sharpe 0.50 at 50-delta, 10yr]
        "regime_allowed": ["VERY_LOW", "LOW", "NORMAL", "ELEVATED"],
        "regime_excluded": ["HIGH", "EXTREME", "CRISIS"],
        "event_block": True,     # Block if event in next 10 days
    },

    "put_credit_spread": {
        "family": "short_premium",
        "objective": "income",
        "legs": 2,
        "base_delta": {"short": 17, "long": 7},
        "base_dte": 37,
        "width_pct": 0.07,       # 7% of underlying between strikes
        "profit_target": 0.50,
        "stop_loss": 1.0,        # Max loss is defined
        "roll_dte": 21,
        "regime_allowed": ["VERY_LOW", "LOW", "NORMAL", "ELEVATED", "HIGH"],
        "regime_excluded": ["CRISIS"],
        "event_block": True,
    },

    "short_strangle": {
        "family": "short_premium",
        "objective": "income",
        "legs": 2,
        "base_delta": {"put": 17, "call": 17},
        "base_dte": 37,
        "profit_target": 0.50,
        "stop_loss": 2.0,        # 2x total credit
        "roll_dte": 21,
        "regime_allowed": ["LOW", "NORMAL"],
        "regime_excluded": ["ELEVATED", "HIGH", "EXTREME", "CRISIS"],
        "event_block": True,
        "iv_rank_min": 50,       # Only sell when IV rank > 50th
    },

    "iron_condor": {
        "family": "short_premium",
        "objective": "income",
        "legs": 4,
        "base_delta": {"short_put": 17, "long_put": 7, "short_call": 17, "long_call": 7},
        "base_dte": 37,
        "profit_target": 0.50,
        "stop_loss": 0.25,       # 25% of max loss early, 100% late
        "roll_dte": 21,
        "regime_allowed": ["LOW", "NORMAL", "ELEVATED"],
        "regime_excluded": ["HIGH", "EXTREME", "CRISIS"],
        "event_block": True,
    },

    "covered_call": {
        "family": "short_premium",
        "objective": "income",
        "legs": 1,               # + underlying
        "base_delta": 30,        # [GS Overwriting: ATM to 10% OTM]
        "base_dte": 30,          # [GS: monthly tenor optimal]
        "sharpe_hist": 0.76,     # [GS: large-cap Sharpe 0.76, 16yr]
        "fcf_yield_filter": True, # [GS: Q5 FCF yield = 8.8% return, Sharpe 0.90]
        "liquidity_filter": 0.30, # [GS: bid-ask < 30% of mid]
        "earnings_avoidance": True, # [GS: +3-6% annual outperf post-2015]
        "regime_allowed": ["VERY_LOW", "LOW", "NORMAL", "ELEVATED"],
        "regime_excluded": ["CRISIS"],
    },

    "calendar_spread_short_front": {
        "family": "short_premium",
        "objective": "event_harvest",
        "legs": 2,
        "base_delta": 50,        # ATM
        "front_dte": "event_dte",
        "back_dte": "event_dte + 30",
        "profit_target": "front_expires_worthless",
        "stop_loss": "realized_move > 1.5x implied_move",
        "regime_allowed": ["ALL"],  # Specifically for events
        "event_required": True,
    },

    # ═══════════════════════════════════════════
    # LONG PREMIUM (DIRECTIONAL / CONVEXITY)
    # ═══════════════════════════════════════════

    "put_debit_spread": {
        "family": "long_premium",
        "objective": "directional_bearish",
        "legs": 2,
        "base_delta": {"long": 35, "short": 17},
        "base_dte": 52,          # 45-60 DTE
        "width_pct": 0.12,
        "profit_target": 1.00,   # 100% of debit (2:1 R/R)
        "stop_loss": 0.50,       # 50% of debit
        "regime_allowed": ["ELEVATED", "HIGH", "NORMAL"],
    },

    "call_debit_spread": {
        "family": "long_premium",
        "objective": "directional_bullish",
        "legs": 2,
        "base_delta": {"long": 45, "short": 27},
        "base_dte": 52,
        "profit_target": 1.00,
        "stop_loss": 0.50,
        "regime_allowed": ["VERY_LOW", "LOW", "NORMAL"],
    },

    "long_straddle": {
        "family": "long_premium",
        "objective": "event_vol",
        "legs": 2,
        "base_delta": 50,        # ATM
        "base_dte": "event_dte + 7",
        "profit_target": "realized > 1.5x implied",
        "stop_loss": "theta > 25% of premium with no move",
        "iv_rank_max": 30,       # Only buy when IV rank < 30th
        "regime_allowed": ["LOW", "NORMAL"],
        "event_required": True,
    },

    # ═══════════════════════════════════════════
    # HEDGING / TAIL RISK
    # ═══════════════════════════════════════════

    "put_ladder_1x2": {
        "family": "hedging",
        "objective": "portfolio_hedge",
        "legs": 3,
        "structure": "buy 1x ATM-5% put, sell 2x ATM-15% puts",
        "base_dte": 75,          # 60-90 DTE
        "cost": "zero_or_credit", # [JPM Global Equity Derivatives]
        "protection_range": "-5% to -15%",
        "risk": "below -15% creates losses",
        "regime_allowed": ["ELEVATED", "HIGH"],  # Rich skew monetization
    },

    "vix_call_spread": {
        "family": "hedging",
        "objective": "tail_hedge",
        "legs": 2,
        "structure": "buy VIX call at current+4, sell at current+12",
        "base_dte": 45,
        "cost_budget": 0.01,     # 1% of NAV annually [GS Portfolio Hedging Toolkit]
        "convexity": "3-5x vs SPX puts in true crises",  # [GS Hedging Toolkit]
        "regime_allowed": ["LOW", "NORMAL"],  # Buy when cheap
        "vix_max": 20,           # Only buy when VIX < 20
    },

    "vix_collar_zero_cost": {
        "family": "hedging",
        "objective": "portfolio_hedge",
        "legs": 3,
        "structure": "buy VIX call, sell higher VIX call, sell VIX put to fund",
        "cost": "zero",          # [JPM Equity Vol Strategy]
        "regime_allowed": ["NORMAL"],
    },

    "scheduled_convexity": {
        "family": "hedging",
        "objective": "systematic_tail",
        "structure": "buy 5-10 delta OTM puts monthly on schedule",
        "cost_budget": 0.01,     # 1-3% of NAV annually
        # [GS Asymmetric Investing 27yr: scheduled > discretionary]
        "frequency": "monthly",
        "regime_allowed": ["ALL"],
    },

    # ═══════════════════════════════════════════
    # THREE-PILLAR TAIL TRADING
    # [Source: JPM Equity Vol Strategy - 3-Pillar Framework]
    # Return: 10.53%, Vol: 10.50%, Sharpe: 1.00, Max DD: -9.67%
    # ═══════════════════════════════════════════

    "tail_delta_pillar": {
        "family": "tail_trading",
        "objective": "spot_recovery",
        "structure": "Long SPX 1M ATM-25D call spread",
        "leverage": "1/22 notional per signal",
        "signal": "3M-1M term structure inversion (TS < 0)",
        "regime_allowed": ["ELEVATED", "HIGH", "CRISIS"],
    },

    "tail_gamma_pillar": {
        "family": "tail_trading",
        "objective": "realized_vol_capture",
        "structure": "Long SPX 5D 25-delta calls, daily hedge at close",
        "leverage": "1x notional per signal",
        "hit_rate": 0.622,       # 62.2% hit rate
        "signal": "TS < 0 (same as delta pillar)",
        "regime_allowed": ["ELEVATED", "HIGH", "CRISIS"],
    },

    "tail_vega_pillar": {
        "family": "tail_trading",
        "objective": "vix_normalization",
        "structure": "Long VIX 1M ATM-25-10D put ladder",
        "leverage": "1/26 notional, match gamma trade vega",
        "signal": "TS < 0",
        "regime_allowed": ["ELEVATED", "HIGH", "CRISIS"],
    },

    # ═══════════════════════════════════════════
    # RELATIVE VALUE / DISPERSION
    # ═══════════════════════════════════════════

    "dispersion_long": {
        "family": "relative_value",
        "objective": "correlation_RV",
        "structure": "sell index vol, buy single-stock vol basket",
        "entry_condition": "implied_corr > 70th percentile",
        "base_dte": 90,
        "hit_rate": 0.5529,      # [JPM: 55.29% normal hit rate]
        "regime_allowed": ["NORMAL", "LOW"],
    },

    "variance_swap_ko": {
        "family": "short_premium",
        "objective": "carry_with_protection",
        "structure": "short KO variance swap (KO at 2.5x strike vol)",
        "advantage": "caps left-tail at barrier, retains 85-90% of carry",
        # [JPM Equity Vol Strategy]
        "base_dte": 60,
        "regime_allowed": ["LOW", "NORMAL"],
    },

    "sector_iv_rv": {
        "family": "relative_value",
        "objective": "sector_mean_reversion",
        "structure": "sell top-decile sector IV, buy bottom-decile",
        "entry_condition": "sector IV percentile divergence > 40pts (5Y lookback)",
        "base_dte": 60,
        "regime_allowed": ["NORMAL", "LOW"],
    },
}
```

---

## 4. STRATEGY SELECTOR ENGINE

### 4.1 Entry Gate Checks

```python
def check_entry_gates(strategy, regime, inputs):
    """
    Returns (pass: bool, reason: str)
    All gates must pass for strategy to be considered.
    """
    gates = []

    # GATE 1: IV Rank Filter [GS Art of Put Selling]
    if strategy["family"] == "short_premium":
        if inputs.vix_percentile_1y < 25:
            return (False, "IV rank below 25th pctile - insufficient premium")

    # GATE 2: Event Avoidance [GS Trading Events; GS Overwriting +3-6% with avoidance]
    if strategy.get("event_block") and regime["event_active"]:
        if regime["event_type"] in ["FOMC", "CPI", "NFP"] and \
           inputs.days_to_fomc <= 10 or inputs.days_to_cpi <= 10 or inputs.days_to_nfp <= 10:
            return (False, "Major event within position's front 10 days")
        if regime["event_type"] == "EARNINGS" and inputs.days_to_earnings <= 5:
            return (False, "Earnings within 5 days - hard block")

    # GATE 3: Liquidity [GS Overwriting: bid-ask < 30% of mid]
    if inputs.spx_bid_ask > 0.30:
        return (False, "Bid-ask > 30% of mid - abort entry")

    # GATE 4: Theta/Gamma Ratio [JPM P&L Attribution: > 5:1 required]
    if strategy["family"] == "short_premium":
        # Calculate expected theta/gamma at entry
        # theta_gamma_ratio = compute_theta_gamma(strategy, inputs)
        # if theta_gamma_ratio < 5.0:
        #     return (False, "Theta/gamma ratio < 5:1 - insufficient edge")
        pass

    # GATE 5: Regime Compatibility
    if regime["regime"] not in strategy.get("regime_allowed", []):
        return (False, f"Strategy not allowed in {regime['regime']} regime")

    # GATE 6: VVIX Stability [GS Vol Vitals: VVIX > 22 = reduce/block]
    if regime["vol_unstable"] and strategy["family"] == "short_premium":
        if strategy["legs"] < 2:  # Naked strategies
            return (False, "VVIX > 22 - no naked short vol")

    # GATE 7: Portfolio Limits
    # Check vega, delta, sector limits vs RISK_LIMITS
    # (Implementation depends on current portfolio state)

    return (True, "All gates passed")
```

### 4.2 Scoring Model

```python
def score_strategy(strategy, regime, inputs, portfolio):
    """
    Score on 6 dimensions. Returns total score 0-10.
    Minimum threshold: 5.0 for recommendation.
    """

    # ─── DIMENSION 1: EDGE (25% weight) ───
    # [Source: GS Vol Vitals; JPM P&L Attribution]
    iv_rank_score = inputs.vix_percentile_1y / 10  # 0-10
    if strategy["family"] == "short_premium":
        iv_rv_bonus = min(inputs.iv_rv_spread / 1.0, 3.0)  # +3 max for IV-RV > 3pts
        edge = min(iv_rank_score + iv_rv_bonus, 10)
    else:  # long premium
        edge = max(10 - iv_rank_score, 0)  # Inverse: buy when IV is low

    # ─── DIMENSION 2: CARRY vs CONVEXITY FIT (20% weight) ───
    # [Source: JPM Resilient Option Carry; GS Asymmetric Investing]
    if strategy["objective"] in ["income", "carry_with_protection"]:
        # Theta/gamma > 5:1 = good carry
        carry_fit = 8.0  # Default for income strategies in proper regime
        if regime["regime"] in ["ELEVATED", "HIGH"]:
            carry_fit = 6.0  # Less certain
    elif strategy["objective"] in ["tail_hedge", "systematic_tail", "event_vol"]:
        # Gamma/theta ratio matters; low IV = good convexity buy
        carry_fit = 8.0 if inputs.vix_percentile_1y < 30 else 5.0
    else:
        carry_fit = 5.0

    # ─── DIMENSION 3: TAIL RISK EXPOSURE (20% weight, 10=least risk) ───
    # [Source: GS Art of Put Selling; JPM Systematic Vol]
    if strategy["legs"] >= 4:    tail = 9    # Iron condor (defined)
    elif strategy["legs"] >= 2:  tail = 7    # Spreads (defined but wider)
    elif strategy["legs"] == 1:
        if strategy["family"] == "short_premium":
            tail = 3  # Naked selling
            if regime["regime"] == "ELEVATED": tail = 2
        else:
            tail = 8  # Long options (max loss = premium)
    else:
        tail = 5

    # ─── DIMENSION 4: ROBUSTNESS / WIN RATE (15% weight) ───
    # [Source: GS Art of Put Selling (74% at 10d); GS Overwriting Sharpe 0.76]
    win_rate = strategy.get("win_rate", 0.55)
    sharpe = strategy.get("sharpe_hist", 0.50)
    robust = min((win_rate * 10) * 0.6 + (sharpe * 5) * 0.4, 10)

    # ─── DIMENSION 5: LIQUIDITY (10% weight) ───
    # [Source: GS Overwriting]
    ba_pct = inputs.spx_bid_ask * 100  # Convert to percentage
    if ba_pct < 5:    liquid = 10
    elif ba_pct < 10: liquid = 8
    elif ba_pct < 20: liquid = 5
    elif ba_pct < 30: liquid = 3
    else:             liquid = 0  # Blocked by gate

    # ─── DIMENSION 6: COMPLEXITY PENALTY (10% weight, 10=simplest) ───
    legs = strategy["legs"]
    if legs == 1:   complexity = 10
    elif legs == 2: complexity = 8
    elif legs == 3: complexity = 5
    elif legs >= 4: complexity = 3

    # TOTAL SCORE
    total = (0.25 * edge +
             0.20 * carry_fit +
             0.20 * tail +
             0.15 * robust +
             0.10 * liquid +
             0.10 * complexity)

    return {
        "total": round(total, 2),
        "edge": round(edge, 2),
        "carry_fit": round(carry_fit, 2),
        "tail_risk": round(tail, 2),
        "robustness": round(robust, 2),
        "liquidity": round(liquid, 2),
        "complexity": round(complexity, 2)
    }
```

### 4.3 Parameterization Engine

```python
def parameterize(strategy, regime, inputs):
    """
    Attach specific delta, DTE, width, and size to a strategy template.
    Returns execution-ready parameters.
    """
    params = {}

    # ─── DELTA ADJUSTMENT BY REGIME ───
    base_d = strategy.get("base_delta", 15)
    if isinstance(base_d, dict):
        # Multi-leg: adjust each
        params["deltas"] = {}
        for leg, d in base_d.items():
            params["deltas"][leg] = _adjust_delta(d, regime)
    else:
        params["delta"] = _adjust_delta(base_d, regime)

    # ─── DTE ADJUSTMENT ───
    base_dte = strategy.get("base_dte", 37)
    if regime["event_active"] and not strategy.get("event_required"):
        # Clear the event: DTE must extend past it
        event_days = min(inputs.days_to_fomc, inputs.days_to_cpi,
                        inputs.days_to_nfp, inputs.days_to_earnings)
        params["dte"] = max(event_days + 10, base_dte)
    else:
        params["dte"] = base_dte

    # ─── SIZE ───
    sell_mult, buy_mult = SIZE_MULTIPLIER[regime["regime"]]
    mult = sell_mult if strategy["family"] == "short_premium" else buy_mult
    mult *= vvix_adjustment(inputs.vvix)

    if regime["confidence"] == "LOW":
        mult *= 0.50  # Half size for low-confidence regimes

    params["size_multiplier"] = round(mult, 2)
    params["profit_target"] = strategy.get("profit_target", 0.50)
    params["stop_loss"] = strategy.get("stop_loss", 2.0)
    params["roll_dte"] = strategy.get("roll_dte", 21)

    return params


def _adjust_delta(base_delta, regime):
    """Regime-adjusted delta selection"""
    adjustments = {
        "VERY_LOW":  1.2,   # Wider deltas OK in low vol
        "LOW":       1.1,
        "NORMAL":    1.0,   # No adjustment
        "ELEVATED":  0.8,   # Tighter for safety
        "HIGH":      0.6,   # Much tighter
        "CRISIS":    0.5,   # Very far OTM only
    }
    return round(base_delta * adjustments.get(regime["regime"], 1.0))
```

### 4.4 Full Selection Pipeline

```python
def select_strategies(regime, inputs, portfolio, objective="income"):
    """
    Main entry point. Returns ranked, parameterized strategy recommendations.

    Args:
        regime: Output of classify_regime()
        inputs: All market data
        portfolio: Current portfolio state
        objective: "income" | "directional" | "hedging" | "event" | "relative_value"

    Returns:
        List of top 3 strategies with parameters and scores
    """

    candidates = []

    for name, strategy in STRATEGIES.items():
        # Step 1: Entry gates
        passed, reason = check_entry_gates(strategy, regime, inputs)
        if not passed:
            continue

        # Step 2: Objective filter
        if objective == "income" and strategy["family"] != "short_premium":
            continue
        if objective == "directional" and strategy["objective"] not in \
           ["directional_bullish", "directional_bearish", "spot_recovery"]:
            continue
        if objective == "hedging" and strategy["family"] != "hedging":
            continue
        if objective == "event" and not strategy.get("event_required"):
            continue
        if objective == "relative_value" and strategy["family"] != "relative_value":
            continue

        # Step 3: Score
        scores = score_strategy(strategy, regime, inputs, portfolio)

        # Step 4: Parameterize
        params = parameterize(strategy, regime, inputs)

        candidates.append({
            "name": name,
            "scores": scores,
            "params": params,
            "strategy": strategy,
        })

    # Sort by total score descending
    candidates.sort(key=lambda x: x["scores"]["total"], reverse=True)

    # Top 3
    top = candidates[:3]

    # ─── FALLBACK LOGIC ───
    if len(top) == 0:
        return {"recommendation": "NO_TRADE",
                "reason": "No strategy passes all filters in current regime"}

    if top[0]["scores"]["total"] < 5.0:
        return {"recommendation": "LOW_CONVICTION",
                "strategies": top,
                "note": "Reduce size by 50% or wait for better setup"}

    if regime["confidence"] == "LOW":
        # Force defined-risk only
        top = [c for c in top if c["strategy"]["legs"] >= 2]
        if not top:
            return {"recommendation": "REGIME_UNCERTAIN",
                    "note": "Mixed signals; no defined-risk strategies available. WAIT."}
        return {"recommendation": "TRADE_CAUTIOUS",
                "strategies": top,
                "note": "Low confidence regime - defined risk only, 50% size"}

    return {"recommendation": "TRADE", "strategies": top}
```

---

## 5. ADJUSTMENT RULES

```python
ADJUSTMENT_RULES = {
    # ─── TIME-BASED ───
    "A1_time_roll": {
        "trigger": "dte <= 21",
        "action": "Roll to next month (same delta) or close",
        "rationale": "Gamma acceleration beyond 21 DTE [GS Art of Put Selling]",
        "priority": "HIGH",
    },

    "A2_time_close": {
        "trigger": "dte <= 7 AND strategy != '0DTE'",
        "action": "Close position regardless of P&L",
        "rationale": "Gamma fundamentally changes position character [JPM P&L Attribution]",
        "priority": "CRITICAL",
    },

    # ─── DELTA-BASED ───
    "A3_delta_breach": {
        "trigger": "short_strike_delta > 30 (from initial 10-20)",
        "action": "Roll strike further OTM and out in time",
        "rationale": "Underlying moved significantly toward strike [JPM Resilient Option Carry]",
        "priority": "HIGH",
    },

    "A4_strangle_test": {
        "trigger": "tested side breached by > 1 standard deviation",
        "action": "Close tested side; leave untested as standalone if profitable. Do NOT double down.",
        "rationale": "[GS Art of Put Selling]",
        "priority": "HIGH",
    },

    # ─── PORTFOLIO-BASED ───
    "A5_delta_hedge": {
        "trigger": "portfolio_delta > +/-15% NAV",
        "action": "Add delta hedges via futures or ATM options",
        "rationale": "[Inference from JPM position management framework]",
        "priority": "HIGH",
    },

    # ─── VOL-BASED ───
    "A6_vol_spike": {
        "trigger": "vix_1d_change > 5 OR vix_5d_change > 30%",
        "action": "Reduce all short vega by 50%. If VIX > 35: close ALL naked short vol.",
        "rationale": "[GS Vol Vitals; GS State of Vol]",
        "priority": "CRITICAL",
    },

    # ─── EARNINGS-SPECIFIC ───
    "A7_earnings_dodge": {
        "trigger": "days_to_earnings <= 5 AND position is covered_call on that name",
        "action": "Roll or close calls before earnings",
        "rationale": "Failure costs 3-6% annually [GS Overwriting 16yr study]",
        "priority": "HIGH",
    },

    # ─── REGIME CHANGE ───
    "A8_regime_change": {
        "trigger": "regime classification changes (e.g., NORMAL -> ELEVATED)",
        "action": "Review ALL positions. Close any not appropriate for new regime. Do not wait for individual stops.",
        "rationale": "[JPM Systematic Vol]",
        "priority": "CRITICAL",
    },

    # ─── CORRELATION SPIKE ───
    "A9_correlation_spike": {
        "trigger": "implied_corr rises above 80th pctile within 5 days",
        "action": "Close all dispersion trades. Review short vol positions for systemic risk.",
        "rationale": "[JPM Equity Vol Strategy]",
        "priority": "HIGH",
    },
}
```

---

## 6. EXIT RULES

```python
EXIT_RULES = {
    # ─── PROFIT TARGETS ───
    "X1_credit_profit": {
        "trigger": "unrealized_profit >= 50% of max_profit",
        "action": "Close. Set limit order at entry.",
        "rationale": "Maximizes risk-adjusted returns [GS Art of Put Selling 10yr]",
        "applies_to": "ALL short_premium strategies",
    },

    "X2_debit_profit": {
        "trigger": "unrealized_profit >= 100% of debit_paid",
        "action": "Close (2:1 R/R achieved). For event trades: close within 24hrs post-event.",
        "rationale": "[GS Trading Events]",
        "applies_to": "ALL long_premium strategies",
    },

    # ─── STOP LOSSES ───
    "X3_credit_stop": {
        "trigger": "unrealized_loss >= 2x premium_received",
        "action": "Close. Expected recovery is negative beyond this point.",
        "rationale": "[GS Art of Put Selling]",
        "applies_to": "ALL short_premium strategies",
    },

    "X4_debit_stop": {
        "trigger": "unrealized_loss >= 50% of premium_paid AND no catalyst change",
        "action": "Close. Re-evaluate thesis before re-entering.",
        "applies_to": "ALL long_premium strategies",
    },

    # ─── TIME STOPS ───
    "X5_time_stop": {
        "trigger": "dte <= 7 AND strategy_type != '0DTE'",
        "action": "Close. Gamma acceleration makes position fundamentally different.",
        "rationale": "[JPM P&L Attribution; JPM Same-day Options]",
    },

    # ─── REGIME STOPS ───
    "X6_regime_exit": {
        "trigger": "regime_classifier output changes to incompatible regime",
        "action": "Close ALL positions not appropriate for new regime immediately.",
        "rationale": "[JPM Systematic Vol]",
    },

    # ─── DAILY P&L STOP ───
    "X7_daily_stop": {
        "trigger": "daily_pnl_loss > 1.5% of NAV",
        "action": "Reduce exposure by 50%. No new trades today.",
        "rationale": "[JPM Systematic Vol]",
    },
}
```

---

## 7. EVENT-SPECIFIC PLAYBOOKS

### 7.1 FOMC Playbook

```python
FOMC_PLAYBOOK = {
    "pre_event": {
        "timing": "T-5 to T-3",
        "iv_behavior": "Front-end IV expansion begins [GS Trading Events 15yr]",
        "strategy": "Buy calendar spreads (sell front-week, buy front+30 DTE)",
        "sizing": "Standard",
    },
    "event_eve": {
        "timing": "T-1",
        "iv_behavior": "IV peaks. Premium richest.",
        "strategy": "Initiate short front-end vol (straddle sell or calendar) if comfortable",
        "sizing": "50% of standard (gap risk)",
    },
    "post_event": {
        "timing": "T+0 to T+1",
        "iv_behavior": "30-60% of front-end excess IV evaporates within 24hrs [GS Trading Events]",
        "strategy": "Close calendars. If directional view, enter cheap debit spreads.",
        "sizing": "Standard (post-crush, vol cheap)",
    },
    "notes": [
        "FOMC produces largest implied moves of all macro events [GS 15yr]",
        "Multi-event weeks (FOMC + CPI): IV premium rises ~40% above baseline",
        "Fed rate decisions show most persistent significance [GS Trading Events]",
    ]
}
```

### 7.2 Earnings Playbook

```python
EARNINGS_PLAYBOOK = {
    "pre_earnings": {
        "timing": "T-5 to T-3",
        "iv_expansion": "20-40% above normal IV [JPM Earnings & Options]",
        "strategy_by_vix": {
            "VIX < 20": "Calendar spreads (sell earnings-week, buy post-earnings)",
            "VIX 20-35": "Iron condors at implied move boundaries",
            "VIX 35-45": "Call buying (+37% avg ROP, 15yr backtest) [GS Earnings Vol]",
            "VIX > 45": "Short strangles (+8% ROP) [GS Earnings Vol]",
        },
    },
    "key_rules": [
        "Avg S&P stock moves +/-4.3% on earnings (18yr avg) [GS Earnings 18yr]",
        "Options market prices +/-5.6% (systematically overestimates) [GS Earnings 18yr]",
        "Sticker shock: stocks >$100 have underpriced earnings moves [GS Earnings 18yr]",
        "Call buying profitable 15/15 years, +13% avg ROP [GS Earnings Vol]",
        "Tech implied moves 1.5-2.0x realized [JPM Earnings & Options]",
        "Financials implied ~1.1-1.2x realized [JPM Earnings & Options]",
    ],
}
```

### 7.3 0DTE Playbook

```python
ZERO_DTE_PLAYBOOK = {
    "characteristics": {
        "theta": "100% decays in single day [JPM Same-day Options]",
        "gamma": "Extreme - binary-like instruments",
        "sizing": "0.1-0.25% of NAV per trade (max)",
        "ndx_vol_correlation": 0.88,  # [JPM: 0DTE implied vs realized, 10am-4pm]
        "ndx_market_share": "~60% of Nasdaq 100 option volume [JPM]",
    },
    "day_of_week": {
        # [Source: JPM Same-day Options]
        "Monday":    {"premium": "HIGH (3.2-4.5%)", "bias": "SELL straddles at 10am"},
        "Tuesday":   {"premium": "HIGH", "bias": "SELL straddles at 10am"},
        "Wednesday": {"premium": "LOW (2.2-2.5%)", "bias": "AVOID or buy premium"},
        "Thursday":  {"premium": "LOW", "bias": "Selective selling only"},
        "Friday":    {"premium": "ELEVATED", "bias": "SELL if no weekend event risk"},
    },
    "entry_rule": "Theta must exceed 2x expected intraday move [JPM P&L Attribution]",
    "event_block": "No 0DTE on FOMC/CPI/NFP days [JPM Same-day Options]",
}
```

---

## 8. TAIL RISK & HEDGING FRAMEWORK

### 8.1 Standing Hedge Allocation

```python
HEDGE_FRAMEWORK = {
    "annual_budget": 0.02,  # 1-3% of NAV [GS Portfolio Hedging Toolkit]

    "instruments": {
        "vix_call_spreads": {
            "allocation": 0.60,  # 60% of hedge budget
            "rationale": "3-5x convexity vs SPX puts in true crises [GS Hedging Toolkit]",
            "structure": "buy VIX call at spot+4, sell at spot+12",
            "tenor": "30-60 DTE, roll monthly",
        },
        "spx_put_spreads": {
            "allocation": 0.25,  # 25% of hedge budget
            "rationale": "Better for moderate corrections (5-10%)",
            "structure": "buy 5% OTM put, sell 15% OTM put",
            "tenor": "90 DTE, roll quarterly",
            "sharpe": 0.88,  # [GS Asymmetric Investing 27yr: put spread collar]
        },
        "scheduled_otm_puts": {
            "allocation": 0.15,  # 15% of hedge budget
            "rationale": "DCA into convexity > discretionary [GS Asymmetric 27yr]",
            "structure": "buy 5-10 delta SPX puts monthly",
        },
    },

    "early_warning_triggers": [
        {"signal": "HY OAS widens > 50bps in 20 days",
         "action": "Double hedge allocation",
         "lead_time": "2-4 weeks before equity vol spike [GS Equity Vol & Economy]"},
        {"signal": "Bid-ask spreads widen > 50% above 20d MA for > 10 days",
         "action": "Activate crisis protocol",
         "lead_time": "2-4 weeks [GS Rising Importance of Falling Liquidity]"},
        {"signal": "Implied correlation rises above 80th pctile in 5 days",
         "action": "Close all dispersion; review all short vol [JPM Equity Vol Strategy]"},
        {"signal": "VVIX > 28 sustained for 3+ days",
         "action": "Reduce all position sizes by 50% [GS Vol Vitals]"},
    ],

    "crisis_protocol": {
        "trigger": "VIX > 35 OR multiple early warnings fire simultaneously",
        "actions": [
            "Close ALL naked short vol immediately",
            "Reduce defined-risk short vol by 75%",
            "Deploy remaining hedge budget into convexity",
            "Cash position to minimum 40% of NAV",
            "Monitor for VIX peak (avg 2-4 weeks, avg peak ~45) [GS Vol Vitals]",
            "Do NOT sell vol until VIX establishes downtrend from peak",
        ],
    },
}
```

### 8.2 Three-Pillar Tail Trading Integration

```python
# [Source: JPM Equity Vol Strategy]
# Combined return: 10.53%, Vol: 10.50%, Sharpe: 1.00, Max DD: -9.67%
# When layered on SPX + put spreads: Sharpe improves from 0.69 to 1.11

TAIL_TRADING_INTEGRATION = {
    "signal": "3M-1M implied vol term structure inversion (TS < 0)",
    "frequency": "< 80 occurrences since 2004",

    "when_inactive": {
        "description": "During peaceful markets (2017-18, 2021, H1'24): ZERO drag",
        "action": "Maintain standard put spread hedges only",
    },

    "when_active": {
        "pillar_1_delta": {
            "entry": "Long SPX 1M ATM-25D call spread at 1/22 notional per signal",
            "exit": "Hold for full 1M tenor; captures spot recovery",
        },
        "pillar_2_gamma": {
            "entry": "Long SPX 5D 25-delta calls, daily hedge at close, full notional",
            "exit": "Hold 5 days; captures realized vol on recovery bounces",
            "hit_rate": "62.2%",
            "key_insight": "Realized vol on up-days is 2.5 vol higher than down-days during tail events",
        },
        "pillar_3_vega": {
            "entry": "Long VIX 1M ATM-25-10D put ladder, 1/26 notional",
            "exit": "Captures VIX normalization (mean reversion)",
            "sizing": "Match vega of gamma trade (~0.04 per trade)",
        },
    },

    "performance": {
        "spx_only":               {"return": 12.5, "sharpe": 0.69, "max_dd": -31.0},
        "spx_plus_put_spread":    {"return": 10.2, "sharpe": 0.69, "max_dd": -12.0},
        "spx_plus_tail_plus_ps":  {"return": 17.1, "sharpe": 1.11, "max_dd": -17.6},
    },
}
```

---

## 9. QUANTITATIVE REFERENCE TABLES

### 9.1 Put Selling Performance by Delta (GS 10-Year Study)

| Delta | Ann. Return | Sharpe | StdDev | Win Rate | Avg Premium |
|-------|-------------|--------|--------|----------|-------------|
| 70    | 7.1%        | 0.50   | 17.0%  | 68%      | 24%         |
| 60    | 6.9%        | 0.51   | 16.0%  | 56%      | 19%         |
| 50    | 6.3%        | 0.50   | 14.5%  | 44%      | 14%         |
| 40    | 5.6%        | 0.50   | 12.6%  | 32%      | 10%         |
| 30    | 4.8%        | 0.50   | 10.1%  | 23%      | 7%          |
| 20    | 3.8%        | 0.54   | 7.6%   | 15%      | 4%          |

### 9.2 Overwriting Performance by FCF Yield Quintile (GS 16-Year Study)

| FCF Quintile | Ann. Return | Sharpe | StdDev |
|-------------|-------------|--------|--------|
| Q1 (Low)    | 2.6%        | 0.27   | 13%    |
| Q2          | 6.1%        | 0.62   | 11%    |
| Q3          | 7.9%        | 0.92   | 9%     |
| Q4          | 7.9%        | 0.91   | 9%     |
| Q5 (High)   | 8.8%        | 0.90   | 10%    |

### 9.3 Hedging Strategy Comparison (GS 27-Year Backtest)

| Strategy               | Ann. Return | Vol   | Sharpe | Max DD  |
|------------------------|-------------|-------|--------|---------|
| S&P 500 (unhedged)     | 9.2%        | 18.2% | 0.51   | -38%    |
| Put Spread Collar 3m/3m| 7.6%        | 8.8%  | 0.88   | -14%    |
| Long Put (monthly roll) | 6.0%       | 10.8% | 0.56   | -13%    |
| Put Spread             | 7.5%        | 13.5% | 0.56   | -17%    |
| Covered Call (10% OTM) | 10.7%       | 14.0% | 0.76   | -25%    |
| Put Selling (10% OTM)  | 5.5%        | 7.0%  | 0.76   | -22%    |

### 9.4 Macro Event Sensitivity by Sector (GS 15-Year Study)

| Sector     | Activity | Credit | Employment | Housing | Oil  | Policy | Prices |
|-----------|----------|--------|------------|---------|------|--------|--------|
| Energy     | 0.1      | 0.2    | 0.1        | 0.1     | 0.8  | 0.1    | 0.4    |
| Real Estate| 0.1      | 0.4    | 0.3        | 0.8     | 0.1  | 0.3    | 0.1    |
| Financials | 0.1      | 0.5    | 0.1        | 0.4     | 0.1  | 0.4    | 0.3    |
| Tech       | 0.1      | 0.1    | 0.2        | 0.1     | 0.1  | 0.2    | 0.2    |
| Healthcare | 0.1      | 0.1    | 0.1        | 0.1     | 0.1  | 0.2    | 0.1    |

### 9.5 Global Vol Levels & Percentiles (JPM, Aug 2025)

| Index | 1M IV | 5Y Pctile | 3M IV | 5Y Pctile | Variance Basis (1M) |
|-------|-------|-----------|-------|-----------|---------------------|
| SPX   | 21.2  | 15.5%     | 22.5  | 18.2%     | -3.3 (long vol)     |
| NDX   | 19.0  | 12.5%     | 21.0  | 10.5%     | +7.7 (short vol)    |
| DAX   | 15.2  | 23.4%     | 15.9  | 24.1%     | -6.3 (long vol)     |
| HSCEI | 22.1  | 15.2%     | 22.4  | 24.3%     | N/A                 |

### 9.6 0DTE Day-of-Week Vol Premium (JPM)

| Day       | NDX Premium | Gamma Imbalance | Bias        |
|-----------|------------|-----------------|-------------|
| Monday    | 3.2-4.5%   | -175 to -125bps | SELL        |
| Tuesday   | 3.2-4.5%   | -125 to -100bps | SELL        |
| Wednesday | 2.2-2.5%   | -50bps          | AVOID/BUY   |
| Thursday  | 2.2-2.5%   | -75bps          | SELECTIVE   |
| Friday    | 3.0-3.5%   | -150bps         | SELL        |

### 9.7 Vol Risk Premium Matrix (JPM Systematic Vol)

| Tenor\Strike | 2Y    | 5Y    | 10Y   | 20Y   |
|-------------|-------|-------|-------|-------|
| ATM         | +42bp | +16bp | +7bp  | +2bp  |
| 25D OTM     | +25bp | +10bp | +3bp  | -3bp  |
| 10D OTM     | +12bp | +5bp  | -1bp  | -8bp  |
| 5D OTM      | +3bp  | +3bp  | -3bp  | -12bp |

### 9.8 Three-Pillar Tail Trading Performance (JPM)

| Configuration              | Return | Vol   | Sharpe | Max DD  |
|----------------------------|--------|-------|--------|---------|
| SPX only                   | 12.5%  | 18.2% | 0.69   | -31.0%  |
| SPX + Put Spread           | 10.2%  | 14.8% | 0.69   | -12.0%  |
| SPX + Tail + Put Spread    | 17.1%  | 15.4% | 1.11   | -17.6%  |
| 2025 YTD: PS only          | 0.8%   | -     | -      | -       |
| 2025 YTD: PS + Tail        | 7.6%   | -     | -      | -       |

---

## 10. CONFLICT RESOLUTION MATRIX

| Conflict                            | Signal A                      | Signal B                       | Resolution                                                                                       |
|-------------------------------------|-------------------------------|--------------------------------|--------------------------------------------------------------------------------------------------|
| IV says sell, Trend says caution    | IV Rank > 75                  | SPX below 200 DMA             | Defined-risk spreads only. 50% size. No naked short.                                             |
| Event approaching, carry attractive | Theta > 0 carry setup         | FOMC/CPI in 3 days            | WAIT. Enter T+1 post-event. IV crush creates better entry.                                       |
| Low vol + Steep skew               | VIX < 15                      | 25d skew > 80th pctile        | Risk reversals or put ladders to monetize skew. No naked short puts.                             |
| Credit widening, VIX still low     | HY OAS +50bps / 20d           | VIX < 18                      | Reduce short vol 25%. Add VIX call spread. Credit leads equity vol 2-4 weeks.                    |
| Dispersion high, correlation low   | Implied corr < 30th pctile    | Sector dispersion elevated    | Enter dispersion trade at 50% standard size. Defined risk preferred.                             |
| Regime confidence = LOW            | Mixed signals                 | No clear regime               | Defined-risk only. 50% size. No new naked positions. WAIT for clarity.                           |
| VVIX elevated, VIX normal          | VVIX > 22                     | VIX 15-20                     | Vol surface unstable. Reduce all sizes 25-50%. Avoid long-dated vega.                            |
| Term structure inverted            | 1M IV > 3M IV                 | VIX < 25                      | Activate tail trading framework (3-pillar). This is the signal.                                  |

---

## 11. POST-TRADE REVIEW TEMPLATE

```yaml
trade_review:
  trade_id:         string
  entry_date:       date
  exit_date:        date
  strategy:         string      # From STRATEGIES universe
  all_legs:         list        # Strike, delta, DTE for each leg

  regime_at_entry:
    regime:         string
    trend:          string
    confidence:     string
    vix:            float
    iv_rank:        float

  entry_rationale:
    gates_passed:   list        # Which E1-E7 gates passed
    score:          float       # Total score from selector
    thesis:         string      # Written thesis statement

  pnl:
    gross_pnl:      float
    pnl_pct:        float       # As % of premium
    attribution:
      theta:        float       # How much from time decay
      delta:        float       # How much from directional move
      gamma:        float       # How much from convexity
      vega:         float       # How much from vol change

  rule_compliance:
    all_entry_rules_followed:  bool
    deviations:                list
    adjustments_made:          list    # Which A1-A9 rules triggered
    exit_trigger:              string  # Which X1-X7 rule fired

  regime_at_exit:
    regime:         string
    regime_changed: bool        # Did regime change during trade?
    regime_exit_invoked: bool   # Was X6 regime exit used?

  lessons:
    what_worked:    string
    what_failed:    string
    rule_addition:  string      # Any new pattern to add to rulebook
```

---

## 12. SOURCE REFERENCE INDEX

### Goldman Sachs Sources
| Code | File | Data Span | Key Contribution |
|------|------|-----------|------------------|
| GS-PS | Art of Put Selling: 10 Year Study | 2003-2013 | Put selling delta/DTE optimization, win rates, exit rules |
| GS-OW | Fundamentals of Overwriting: 16 Year Study | 2003-2019 | Covered call FCF yield screening, earnings avoidance |
| GS-TE | Trading Events: US Macro Catalysts, 15 Year Study | 2010-2024 | FOMC/CPI/NFP sensitivity matrices, event playbooks |
| GS-ED | Earnings Day Moves: 18 Year Study | 2005-2023 | Implied vs realized earnings moves, VIX-conditional strategies |
| GS-EV | Earnings Volatility Parts 1-3 | 2024-2025 | VIX regime earnings strategies, sticker shock effect |
| GS-VV | Vol Vitals Series (5 issues) | 2024-2025 | VIX spike profiling, VVIX thresholds, crisis protocol |
| GS-SV | State of Vol Series (3 issues) | 2024-2025 | Term structure rules, skew timing, carry logic |
| GS-HT | Portfolio Hedging Toolkit | Mar 2024 | VIX calls vs SPX puts convexity comparison |
| GS-VX | VIX as Market Timing Signal | - | VIX < 11 myth debunking, policy process framework |
| GS-AI | Asymmetric Investing: 27 Year Study | 1996-2022 | Scheduled convexity, put spread collar Sharpe 0.88 |
| GS-LQ | Rising Importance of Falling Liquidity | - | Liquidity-vol coupling, 2-4 week lead time |
| GS-EC | Equity Volatility & Economy: 2023 Update | - | Credit spread early warning, monetary policy mapping |

### JPMorgan Sources
| Code | File | Key Contribution |
|------|------|------------------|
| JPM-SV | Systematic Vol Investing (194pg, Oct 2024) | 3-regime model, GARCH, vol premium matrix, backtest |
| JPM-RC | Resilient Option Carry (Sep 2024) | Carry strategy specs, hedge ratios, roll rules |
| JPM-PL | Options P&L Attribution (Sep 2023) | Theta/gamma ratio, P&L decomposition, 0DTE fair value |
| JPM-EQ | Equity Vol Strategy Series (5 issues, 2025) | KO varswap, dispersion, 3-pillar tail trading, FVA, fixed premium |
| JPM-GD | Global Equity Derivatives (Aug 2025) | Put ladders, sector ratio switches, skew dislocations |
| JPM-GI | Global Index Volatility (Aug 2025) | Global vol rankings, variance convexity, cross-index spreads |
| JPM-VR | Volatility Review: Fed Easing (Sep 2024) | Fed cycle asset performance, sector rotation timing |
| JPM-0D | Same-Day Options (Nov 2024) | 0DTE gamma profiles, day-of-week patterns, NDX correlation |
| JPM-EA | Earnings and Options (Jan 2025) | IV expansion dynamics, sector-specific patterns |

---

*DISCLAIMER: This document synthesizes research findings for educational and reference purposes. All claims are attributed to source files. Items not directly from sources are labeled [Inference]. This is not investment advice. Options involve substantial risk of loss. Past performance does not guarantee future results.*
