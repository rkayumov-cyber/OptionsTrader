"""Decision engine data models.

Models for the options trading decision engine: regime classification,
strategy selection, position sizing, adjustment/exit rules, event playbooks,
tail risk management, and conflict resolution.

Based on Goldman Sachs and JPMorgan derivatives research (2003-2025).
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enumerations ──────────────────────────────────────────────────────────


class VolRegime(str, Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    CRISIS = "CRISIS"
    LIQUIDITY_STRESS = "LIQUIDITY_STRESS"


class Trend(str, Enum):
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    RANGE_BOUND = "RANGE_BOUND"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EventType(str, Enum):
    FOMC = "FOMC"
    CPI = "CPI"
    NFP = "NFP"
    EARNINGS = "EARNINGS"
    NONE = "NONE"


class StrategyFamily(str, Enum):
    SHORT_PREMIUM = "short_premium"
    LONG_PREMIUM = "long_premium"
    HEDGING = "hedging"
    TAIL_TRADING = "tail_trading"
    RELATIVE_VALUE = "relative_value"


class StrategyObjective(str, Enum):
    INCOME = "income"
    DIRECTIONAL_BULLISH = "directional_bullish"
    DIRECTIONAL_BEARISH = "directional_bearish"
    EVENT_HARVEST = "event_harvest"
    EVENT_VOL = "event_vol"
    PORTFOLIO_HEDGE = "portfolio_hedge"
    TAIL_HEDGE = "tail_hedge"
    SYSTEMATIC_TAIL = "systematic_tail"
    SPOT_RECOVERY = "spot_recovery"
    REALIZED_VOL_CAPTURE = "realized_vol_capture"
    VIX_NORMALIZATION = "vix_normalization"
    CORRELATION_RV = "correlation_RV"
    CARRY_WITH_PROTECTION = "carry_with_protection"
    SECTOR_MEAN_REVERSION = "sector_mean_reversion"


class RulePriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RecommendationType(str, Enum):
    TRADE = "TRADE"
    TRADE_CAUTIOUS = "TRADE_CAUTIOUS"
    LOW_CONVICTION = "LOW_CONVICTION"
    NO_TRADE = "NO_TRADE"
    REGIME_UNCERTAIN = "REGIME_UNCERTAIN"


class PlaybookPhase(str, Enum):
    PRE_EVENT = "pre_event"
    EVENT_EVE = "event_eve"
    POST_EVENT = "post_event"


class DayOfWeek(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"


# ── Market Inputs (Section 1.1) ──────────────────────────────────────────


class SpotData(BaseModel):
    spx_level: float = Field(description="Current SPX price")
    spx_ret_1d: float = Field(0.0, description="1-day return")
    spx_ret_5d: float = Field(0.0, description="5-day return")
    spx_ret_20d: float = Field(0.0, description="20-day return")
    spx_sma_50: float = Field(description="50-day simple moving average")
    spx_sma_200: float = Field(description="200-day simple moving average")
    breadth_pct_above_50dma: float = Field(
        50.0, description="Pct of stocks above 50 DMA"
    )


class VolData(BaseModel):
    vix: float = Field(description="VIX spot level")
    vix_1d_change: float = Field(0.0, description="VIX 1-day change (points)")
    vix_5d_change: float = Field(0.0, description="VIX 5-day change (points)")
    vix_percentile_1y: float = Field(
        50.0, description="VIX percentile rank over 1 year (0-100)"
    )
    vvix: float = Field(18.0, description="CBOE VVIX (vol of vol)")
    vix9d: float = Field(0.0, description="9-day VIX")
    iv_atm_1m: float = Field(0.0, description="1-month ATM implied vol")
    iv_atm_3m: float = Field(0.0, description="3-month ATM implied vol")
    iv_atm_6m: float = Field(0.0, description="6-month ATM implied vol")
    rv_10d: float = Field(0.0, description="10-day realized vol")
    rv_20d: float = Field(0.0, description="20-day realized vol")
    rv_30d: float = Field(0.0, description="30-day realized vol")
    iv_rv_spread: float = Field(0.0, description="iv_atm_1m - rv_20d")


class SkewData(BaseModel):
    put_skew_25d_1m: float = Field(5.0, description="25-delta 1M put skew")
    put_skew_25d_3m: float = Field(5.0, description="25-delta 3M put skew")
    risk_reversal_25d: float = Field(0.0, description="25-delta risk reversal cost")
    skew_pctile_1y: float = Field(50.0, description="Skew percentile (1Y lookback)")


class TermStructureData(BaseModel):
    ts_1m_3m: float = Field(0.0, description="3M IV - 1M IV (contango if positive)")
    ts_3m_6m: float = Field(0.0, description="6M IV - 3M IV")
    ts_slope: float = Field(0.0, description="Overall term structure slope")
    vix_futures_1m: float = Field(0.0, description="VIX 1M future")
    vix_futures_3m: float = Field(0.0, description="VIX 3M future")
    roll_yield: float = Field(0.0, description="(VIX_future - VIX_spot) / VIX_spot")


class EventCalendarData(BaseModel):
    days_to_fomc: int = Field(30, description="Trading days to next FOMC")
    days_to_cpi: int = Field(30, description="Trading days to next CPI")
    days_to_nfp: int = Field(30, description="Trading days to next NFP")
    days_to_earnings: int = Field(
        30, description="Trading days to next relevant earnings"
    )
    events_next_5d: int = Field(0, description="Major events in next 5 trading days")
    events_next_20d: int = Field(0, description="Major events in next 20 trading days")


class CreditMacroData(BaseModel):
    hy_oas: float = Field(400.0, description="High yield OAS spread (bps)")
    hy_oas_20d_change: float = Field(0.0, description="HY OAS 20-day change (bps)")
    ig_spread: float = Field(100.0, description="Investment grade spread (bps)")
    fed_funds_rate: float = Field(5.0, description="Current fed funds rate")
    us_10y_yield: float = Field(4.0, description="10Y Treasury yield")
    us_2s10s: float = Field(0.0, description="2s10s yield curve slope")


class LiquidityData(BaseModel):
    spx_bid_ask: float = Field(
        0.05, description="SPX options bid-ask as pct of mid"
    )
    spx_bid_ask_20d_ma: float = Field(0.05, description="20-day MA of bid-ask")
    bid_ask_widening: float = Field(
        1.0, description="Current / 20d MA ratio (>1 = widening)"
    )
    emini_depth: float = Field(1000.0, description="E-mini market depth (contracts)")
    options_volume_oi: float = Field(0.5, description="Volume / Open Interest ratio")


class CorrelationData(BaseModel):
    implied_corr: float = Field(50.0, description="Implied correlation")
    realized_corr_20d: float = Field(50.0, description="20-day realized correlation")
    corr_pctile_1y: float = Field(50.0, description="Correlation percentile (1Y)")
    dispersion: float = Field(
        0.0, description="implied_corr - realized_corr_20d"
    )


class MarketInputs(BaseModel):
    """All market data inputs for the decision engine (Section 1.1)."""

    spot: SpotData = Field(default_factory=SpotData)
    vol: VolData
    skew: SkewData = Field(default_factory=SkewData)
    term_structure: TermStructureData = Field(default_factory=TermStructureData)
    events: EventCalendarData = Field(default_factory=EventCalendarData)
    credit: CreditMacroData = Field(default_factory=CreditMacroData)
    liquidity: LiquidityData = Field(default_factory=LiquidityData)
    correlation: CorrelationData = Field(default_factory=CorrelationData)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Regime Result (Section 1.2) ──────────────────────────────────────────


class RegimeResult(BaseModel):
    """Output of the regime classifier."""

    regime: VolRegime
    trend: Trend = Trend.RANGE_BOUND
    event_active: bool = False
    event_type: EventType = EventType.NONE
    multi_event: bool = False
    vol_unstable: bool = False
    confidence: Confidence = Confidence.MEDIUM
    confirming_signals: int = 0
    actions: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Position Sizing (Section 2) ──────────────────────────────────────────


class SizeMultipliers(BaseModel):
    """Regime-based sell/buy premium multipliers."""

    sell_premium: float = Field(ge=0, le=1)
    buy_premium: float = Field(ge=0, le=1)
    vvix_adjustment: float = Field(ge=0, le=1)
    confidence_adjustment: float = Field(ge=0, le=1)
    final_sell: float = Field(ge=0, le=1)
    final_buy: float = Field(ge=0, le=1)


class PositionSizeResult(BaseModel):
    """Output of the position sizer."""

    premium_budget: float = Field(description="Dollar premium budget for this trade")
    size_multiplier: float = Field(description="Combined multiplier applied")
    multiplier_breakdown: SizeMultipliers
    risk_limit_breaches: list[str] = Field(default_factory=list)
    within_limits: bool = True


class RiskLimits(BaseModel):
    """Portfolio-level risk limits."""

    max_portfolio_vega: float = 0.005
    max_portfolio_delta: float = 0.20
    max_portfolio_gamma_t7: float = 0.003
    max_single_name_pct: float = 0.05
    max_sector_pct: float = 0.20
    max_correlated_positions: int = 3
    daily_pnl_stop: float = 0.015
    weekly_pnl_stop: float = 0.030
    cash_reserve_min: float = 0.20


# ── Strategy Templates (Section 3) ───────────────────────────────────────


class StrategyTemplate(BaseModel):
    """A strategy template from the strategy universe."""

    name: str
    family: StrategyFamily
    objective: StrategyObjective
    legs: int
    base_delta: int | dict[str, int] = 15
    base_dte: int | str = 37
    width_pct: float | None = None
    profit_target: float | str = 0.50
    stop_loss: float | str = 2.0
    roll_dte: int | None = 21
    win_rate: float | None = None
    sharpe_hist: float | None = None
    regime_allowed: list[str] = Field(default_factory=lambda: ["ALL"])
    regime_excluded: list[str] = Field(default_factory=list)
    event_block: bool = False
    event_required: bool = False
    iv_rank_min: int | None = None
    iv_rank_max: int | None = None
    vix_max: float | None = None
    structure: str | None = None
    cost: str | None = None
    cost_budget: float | None = None
    description: str = ""


# ── Selector Output (Section 4) ──────────────────────────────────────────


class StrategyScore(BaseModel):
    """6-dimension strategy score."""

    total: float = Field(ge=0, le=10)
    edge: float = Field(ge=0, le=10)
    carry_fit: float = Field(ge=0, le=10)
    tail_risk: float = Field(ge=0, le=10)
    robustness: float = Field(ge=0, le=10)
    liquidity: float = Field(ge=0, le=10)
    complexity: float = Field(ge=0, le=10)


class StrategyParams(BaseModel):
    """Execution-ready strategy parameters."""

    delta: int | None = None
    deltas: dict[str, int] | None = None
    dte: int = 37
    size_multiplier: float = 1.0
    profit_target: float | str = 0.50
    stop_loss: float | str = 2.0
    roll_dte: int | None = 21


class GateCheckResult(BaseModel):
    """Result of a single entry gate check."""

    gate_name: str
    passed: bool
    reason: str = ""


class StrategyCandidate(BaseModel):
    """A scored, parameterized strategy candidate."""

    name: str
    template: StrategyTemplate
    scores: StrategyScore
    params: StrategyParams
    gates: list[GateCheckResult] = Field(default_factory=list)


class StrategyRecommendation(BaseModel):
    """Final output of the strategy selector."""

    recommendation: RecommendationType
    strategies: list[StrategyCandidate] = Field(default_factory=list)
    regime: RegimeResult
    note: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Adjustment Rules (Section 5) ─────────────────────────────────────────


class AdjustmentRule(BaseModel):
    """An adjustment rule definition (A1-A9)."""

    rule_id: str = Field(description="e.g. A1, A2, ...")
    name: str
    trigger: str
    action: str
    rationale: str = ""
    priority: RulePriority = RulePriority.HIGH


class RuleEvaluation(BaseModel):
    """Result of evaluating a rule against a position."""

    rule_id: str
    rule_name: str
    triggered: bool
    priority: RulePriority
    action: str = ""
    details: str = ""


# ── Exit Rules (Section 6) ───────────────────────────────────────────────


class ExitRule(BaseModel):
    """An exit rule definition (X1-X7)."""

    rule_id: str = Field(description="e.g. X1, X2, ...")
    name: str
    trigger: str
    action: str
    rationale: str = ""
    applies_to: str = "ALL"


# ── Event Playbooks (Section 7) ──────────────────────────────────────────


class PlaybookPhaseDetail(BaseModel):
    """A single phase of an event playbook."""

    phase: PlaybookPhase
    timing: str
    iv_behavior: str = ""
    strategy: str
    sizing: str = "Standard"
    notes: list[str] = Field(default_factory=list)


class EventPlaybook(BaseModel):
    """Complete event playbook."""

    event_type: EventType
    phases: list[PlaybookPhaseDetail]
    notes: list[str] = Field(default_factory=list)
    key_rules: list[str] = Field(default_factory=list)


class ZeroDTEDayInfo(BaseModel):
    """0DTE day-of-week recommendation."""

    day: DayOfWeek
    premium: str
    bias: str
    gamma_imbalance: str = ""


class ZeroDTEPlaybook(BaseModel):
    """0DTE trading playbook."""

    characteristics: dict[str, Any] = Field(default_factory=dict)
    days: list[ZeroDTEDayInfo] = Field(default_factory=list)
    entry_rule: str = ""
    event_block: str = ""


# ── Tail Risk (Section 8) ────────────────────────────────────────────────


class HedgeInstrument(BaseModel):
    """A single hedge instrument allocation."""

    name: str
    allocation: float = Field(description="Fraction of hedge budget")
    structure: str
    tenor: str = ""
    rationale: str = ""


class HedgeAllocation(BaseModel):
    """Standing hedge allocation."""

    annual_budget_pct: float = 0.02
    instruments: list[HedgeInstrument] = Field(default_factory=list)


class EarlyWarningSignal(BaseModel):
    """An early warning signal for tail risk."""

    signal: str
    action: str
    lead_time: str = ""
    triggered: bool = False
    current_value: float | None = None
    threshold: float | None = None


class TailTradingStatus(BaseModel):
    """Status of the 3-pillar tail trading framework."""

    signal_active: bool = Field(
        description="True if 3M-1M term structure inverted"
    )
    ts_value: float = Field(0.0, description="Current 3M-1M term structure value")
    delta_pillar_active: bool = False
    gamma_pillar_active: bool = False
    vega_pillar_active: bool = False


class TailRiskAssessment(BaseModel):
    """Full tail risk assessment output."""

    hedge_allocation: HedgeAllocation
    early_warnings: list[EarlyWarningSignal] = Field(default_factory=list)
    active_warnings_count: int = 0
    crisis_protocol_active: bool = False
    crisis_actions: list[str] = Field(default_factory=list)
    tail_trading: TailTradingStatus = Field(default_factory=TailTradingStatus)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Conflict Resolution (Section 10) ─────────────────────────────────────


class ConflictScenario(BaseModel):
    """A conflict scenario from the resolution matrix."""

    conflict_id: str
    description: str
    signal_a: str
    signal_b: str
    resolution: str
    detected: bool = False


# ── Post-Trade Review (Section 11) ───────────────────────────────────────


class PnLAttribution(BaseModel):
    """P&L attribution across Greeks."""

    theta: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    vega: float = 0.0
    total: float = 0.0


class PostTradeReview(BaseModel):
    """Post-trade review record."""

    trade_id: str
    entry_date: date
    exit_date: date | None = None
    strategy: str
    legs: list[dict[str, Any]] = Field(default_factory=list)

    regime_at_entry: RegimeResult
    regime_at_exit: RegimeResult | None = None
    regime_changed: bool = False

    entry_score: float = 0.0
    entry_thesis: str = ""
    gates_passed: list[str] = Field(default_factory=list)

    gross_pnl: float = 0.0
    pnl_pct: float = 0.0
    attribution: PnLAttribution = Field(default_factory=PnLAttribution)

    adjustments_made: list[str] = Field(default_factory=list)
    exit_trigger: str = ""
    all_rules_followed: bool = True
    deviations: list[str] = Field(default_factory=list)

    what_worked: str = ""
    what_failed: str = ""
    rule_addition: str = ""


# ── Reference Table Entries ───────────────────────────────────────────────


class PutSellingPerformance(BaseModel):
    """Put selling performance by delta (GS 10yr)."""

    delta: int
    ann_return: float
    sharpe: float
    std_dev: float
    win_rate: float
    avg_premium: float


class OverwritingPerformance(BaseModel):
    """Overwriting performance by FCF yield quintile (GS 16yr)."""

    fcf_quintile: str
    ann_return: float
    sharpe: float
    std_dev: float


class HedgingComparison(BaseModel):
    """Hedging strategy comparison (GS 27yr)."""

    strategy: str
    ann_return: float
    vol: float
    sharpe: float
    max_dd: float


class SectorEventSensitivity(BaseModel):
    """Sector sensitivity to macro events (GS 15yr)."""

    sector: str
    activity: float
    credit: float
    employment: float
    housing: float
    oil: float
    policy: float
    prices: float


class GlobalVolLevel(BaseModel):
    """Global vol level and percentile (JPM)."""

    index: str
    iv_1m: float
    pctile_1m_5y: float
    iv_3m: float
    pctile_3m_5y: float
    variance_basis_1m: float


class ZeroDTEVolPremium(BaseModel):
    """0DTE day-of-week vol premium (JPM)."""

    day: str
    ndx_premium: str
    gamma_imbalance: str
    bias: str


class VolRiskPremium(BaseModel):
    """Vol risk premium by tenor and strike (JPM)."""

    tenor: str
    atm: float
    otm_25d: float
    otm_10d: float
    otm_5d: float


class TailTradingPerformance(BaseModel):
    """3-pillar tail trading performance (JPM)."""

    configuration: str
    ann_return: float
    vol: float | None = None
    sharpe: float | None = None
    max_dd: float | None = None


# ── Full Analysis Output ─────────────────────────────────────────────────


class PositionHealthCheck(BaseModel):
    """Health check for a single position."""

    position_id: str
    adjustment_rules: list[RuleEvaluation] = Field(default_factory=list)
    exit_rules: list[RuleEvaluation] = Field(default_factory=list)
    triggered_count: int = 0
    critical_count: int = 0
    recommended_action: str = ""


class FullAnalysisResult(BaseModel):
    """Complete decision engine analysis."""

    regime: RegimeResult
    recommendation: StrategyRecommendation
    tail_risk: TailRiskAssessment
    conflicts: list[ConflictScenario] = Field(default_factory=list)
    active_playbook: EventPlaybook | None = None
    position_health: list[PositionHealthCheck] = Field(default_factory=list)
    market_inputs: MarketInputs
    timestamp: datetime = Field(default_factory=datetime.utcnow)
