"""Strategy universe (Section 3).

20+ strategy templates as constant data: CSP, put spread, iron condor,
straddle, calendar, VIX hedges, tail pillars, dispersion, etc.
"""

from mcp_server.engine_models import (
    StrategyFamily,
    StrategyObjective,
    StrategyTemplate,
)


class StrategyUniverse:
    """Complete strategy template catalog."""

    TEMPLATES: dict[str, StrategyTemplate] = {
        # ═══ SHORT PREMIUM (INCOME / CARRY) ═══
        "cash_secured_put": StrategyTemplate(
            name="cash_secured_put",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.INCOME,
            legs=1,
            base_delta=12,
            base_dte=37,
            profit_target=0.50,
            stop_loss=2.0,
            roll_dte=21,
            win_rate=0.74,
            sharpe_hist=0.50,
            regime_allowed=["VERY_LOW", "LOW", "NORMAL", "ELEVATED"],
            regime_excluded=["HIGH", "EXTREME", "CRISIS"],
            event_block=True,
            description="GS Art of Put Selling: 10-15 delta, 74% win rate, 30-45 DTE",
        ),
        "put_credit_spread": StrategyTemplate(
            name="put_credit_spread",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.INCOME,
            legs=2,
            base_delta={"short": 17, "long": 7},
            base_dte=37,
            width_pct=0.07,
            profit_target=0.50,
            stop_loss=1.0,
            roll_dte=21,
            regime_allowed=["VERY_LOW", "LOW", "NORMAL", "ELEVATED", "HIGH"],
            regime_excluded=["CRISIS"],
            event_block=True,
            description="Defined-risk put spread, 7% width between strikes",
        ),
        "short_strangle": StrategyTemplate(
            name="short_strangle",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.INCOME,
            legs=2,
            base_delta={"put": 17, "call": 17},
            base_dte=37,
            profit_target=0.50,
            stop_loss=2.0,
            roll_dte=21,
            regime_allowed=["LOW", "NORMAL"],
            regime_excluded=["ELEVATED", "HIGH", "EXTREME", "CRISIS"],
            event_block=True,
            iv_rank_min=50,
            description="Naked strangle, only in low/normal vol with IV rank > 50th",
        ),
        "iron_condor": StrategyTemplate(
            name="iron_condor",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.INCOME,
            legs=4,
            base_delta={"short_put": 17, "long_put": 7, "short_call": 17, "long_call": 7},
            base_dte=37,
            profit_target=0.50,
            stop_loss=0.25,
            roll_dte=21,
            regime_allowed=["LOW", "NORMAL", "ELEVATED"],
            regime_excluded=["HIGH", "EXTREME", "CRISIS"],
            event_block=True,
            description="4-leg defined-risk; close at 50% profit or 25% of max loss early",
        ),
        "covered_call": StrategyTemplate(
            name="covered_call",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.INCOME,
            legs=1,
            base_delta=30,
            base_dte=30,
            sharpe_hist=0.76,
            regime_allowed=["VERY_LOW", "LOW", "NORMAL", "ELEVATED"],
            regime_excluded=["CRISIS"],
            description="GS Overwriting: large-cap Sharpe 0.76, Q5 FCF yield = 8.8%",
        ),
        "calendar_spread_short_front": StrategyTemplate(
            name="calendar_spread_short_front",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.EVENT_HARVEST,
            legs=2,
            base_delta=50,
            base_dte="event_dte",
            profit_target="front_expires_worthless",
            stop_loss="realized_move > 1.5x implied_move",
            regime_allowed=["ALL"],
            event_required=True,
            description="ATM calendar selling front-end event IV, buying back-month",
        ),
        # ═══ LONG PREMIUM (DIRECTIONAL / CONVEXITY) ═══
        "put_debit_spread": StrategyTemplate(
            name="put_debit_spread",
            family=StrategyFamily.LONG_PREMIUM,
            objective=StrategyObjective.DIRECTIONAL_BEARISH,
            legs=2,
            base_delta={"long": 35, "short": 17},
            base_dte=52,
            width_pct=0.12,
            profit_target=1.00,
            stop_loss=0.50,
            regime_allowed=["ELEVATED", "HIGH", "NORMAL"],
            description="Bearish debit spread, 45-60 DTE, 2:1 R/R target",
        ),
        "call_debit_spread": StrategyTemplate(
            name="call_debit_spread",
            family=StrategyFamily.LONG_PREMIUM,
            objective=StrategyObjective.DIRECTIONAL_BULLISH,
            legs=2,
            base_delta={"long": 45, "short": 27},
            base_dte=52,
            profit_target=1.00,
            stop_loss=0.50,
            regime_allowed=["VERY_LOW", "LOW", "NORMAL"],
            description="Bullish debit spread, 45-60 DTE, 2:1 R/R target",
        ),
        "long_straddle": StrategyTemplate(
            name="long_straddle",
            family=StrategyFamily.LONG_PREMIUM,
            objective=StrategyObjective.EVENT_VOL,
            legs=2,
            base_delta=50,
            base_dte="event_dte + 7",
            profit_target="realized > 1.5x implied",
            stop_loss="theta > 25% of premium with no move",
            iv_rank_max=30,
            regime_allowed=["LOW", "NORMAL"],
            event_required=True,
            description="ATM straddle for event vol, only when IV rank < 30th",
        ),
        # ═══ HEDGING / TAIL RISK ═══
        "put_ladder_1x2": StrategyTemplate(
            name="put_ladder_1x2",
            family=StrategyFamily.HEDGING,
            objective=StrategyObjective.PORTFOLIO_HEDGE,
            legs=3,
            structure="buy 1x ATM-5% put, sell 2x ATM-15% puts",
            base_dte=75,
            cost="zero_or_credit",
            regime_allowed=["ELEVATED", "HIGH"],
            description="Put ladder monetizing rich skew, protection -5% to -15%",
        ),
        "vix_call_spread": StrategyTemplate(
            name="vix_call_spread",
            family=StrategyFamily.HEDGING,
            objective=StrategyObjective.TAIL_HEDGE,
            legs=2,
            structure="buy VIX call at current+4, sell at current+12",
            base_dte=45,
            cost_budget=0.01,
            regime_allowed=["LOW", "NORMAL"],
            vix_max=20,
            description="3-5x convexity vs SPX puts in crises (GS Hedging Toolkit)",
        ),
        "vix_collar_zero_cost": StrategyTemplate(
            name="vix_collar_zero_cost",
            family=StrategyFamily.HEDGING,
            objective=StrategyObjective.PORTFOLIO_HEDGE,
            legs=3,
            structure="buy VIX call, sell higher VIX call, sell VIX put to fund",
            cost="zero",
            regime_allowed=["NORMAL"],
            description="Zero-cost VIX collar (JPM Equity Vol Strategy)",
        ),
        "scheduled_convexity": StrategyTemplate(
            name="scheduled_convexity",
            family=StrategyFamily.HEDGING,
            objective=StrategyObjective.SYSTEMATIC_TAIL,
            legs=1,
            structure="buy 5-10 delta OTM puts monthly on schedule",
            cost_budget=0.01,
            regime_allowed=["ALL"],
            description="GS Asymmetric 27yr: scheduled > discretionary convexity",
        ),
        # ═══ THREE-PILLAR TAIL TRADING (JPM) ═══
        "tail_delta_pillar": StrategyTemplate(
            name="tail_delta_pillar",
            family=StrategyFamily.TAIL_TRADING,
            objective=StrategyObjective.SPOT_RECOVERY,
            legs=2,
            structure="Long SPX 1M ATM-25D call spread",
            regime_allowed=["ELEVATED", "HIGH", "CRISIS"],
            description="Pillar 1: captures spot recovery, 1/22 notional per signal",
        ),
        "tail_gamma_pillar": StrategyTemplate(
            name="tail_gamma_pillar",
            family=StrategyFamily.TAIL_TRADING,
            objective=StrategyObjective.REALIZED_VOL_CAPTURE,
            legs=1,
            structure="Long SPX 5D 25-delta calls, daily hedge at close",
            win_rate=0.622,
            regime_allowed=["ELEVATED", "HIGH", "CRISIS"],
            description="Pillar 2: 62.2% hit rate capturing realized vol on recovery bounces",
        ),
        "tail_vega_pillar": StrategyTemplate(
            name="tail_vega_pillar",
            family=StrategyFamily.TAIL_TRADING,
            objective=StrategyObjective.VIX_NORMALIZATION,
            legs=3,
            structure="Long VIX 1M ATM-25-10D put ladder",
            regime_allowed=["ELEVATED", "HIGH", "CRISIS"],
            description="Pillar 3: VIX mean reversion, 1/26 notional, match gamma vega",
        ),
        # ═══ RELATIVE VALUE / DISPERSION ═══
        "dispersion_long": StrategyTemplate(
            name="dispersion_long",
            family=StrategyFamily.RELATIVE_VALUE,
            objective=StrategyObjective.CORRELATION_RV,
            legs=2,
            structure="sell index vol, buy single-stock vol basket",
            base_dte=90,
            win_rate=0.5529,
            regime_allowed=["NORMAL", "LOW"],
            description="JPM: 55.29% normal hit rate, enter when implied corr > 70th pctile",
        ),
        "variance_swap_ko": StrategyTemplate(
            name="variance_swap_ko",
            family=StrategyFamily.SHORT_PREMIUM,
            objective=StrategyObjective.CARRY_WITH_PROTECTION,
            legs=1,
            structure="short KO variance swap (KO at 2.5x strike vol)",
            base_dte=60,
            regime_allowed=["LOW", "NORMAL"],
            description="JPM: caps left-tail at barrier, retains 85-90% of carry",
        ),
        "sector_iv_rv": StrategyTemplate(
            name="sector_iv_rv",
            family=StrategyFamily.RELATIVE_VALUE,
            objective=StrategyObjective.SECTOR_MEAN_REVERSION,
            legs=2,
            structure="sell top-decile sector IV, buy bottom-decile",
            base_dte=60,
            regime_allowed=["NORMAL", "LOW"],
            description="Sector IV divergence > 40pts (5Y lookback) mean reversion",
        ),
    }

    @classmethod
    def get(cls, name: str) -> StrategyTemplate:
        """Get a strategy template by name."""
        tpl = cls.TEMPLATES.get(name)
        if tpl is None:
            raise ValueError(
                f"Unknown strategy '{name}'. Available: {list(cls.TEMPLATES.keys())}"
            )
        return tpl

    @classmethod
    def list_all(cls) -> list[StrategyTemplate]:
        """Return all strategy templates."""
        return list(cls.TEMPLATES.values())

    @classmethod
    def by_family(cls, family: StrategyFamily) -> list[StrategyTemplate]:
        """Filter strategies by family."""
        return [s for s in cls.TEMPLATES.values() if s.family == family]

    @classmethod
    def by_objective(cls, objective: StrategyObjective) -> list[StrategyTemplate]:
        """Filter strategies by objective."""
        return [s for s in cls.TEMPLATES.values() if s.objective == objective]

    @classmethod
    def names(cls) -> list[str]:
        """Return all strategy names."""
        return list(cls.TEMPLATES.keys())
