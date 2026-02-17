"""Data models for market data."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


Market = Literal["US", "JP", "HK"]
OptionType = Literal["call", "put"]


class Greeks(BaseModel):
    """Option Greeks."""

    delta: float = Field(description="Rate of change of option price vs underlying")
    gamma: float = Field(description="Rate of change of delta")
    theta: float = Field(description="Time decay per day")
    vega: float = Field(description="Sensitivity to volatility")
    rho: float = Field(description="Sensitivity to interest rate")


class Quote(BaseModel):
    """Real-time price quote."""

    symbol: str
    market: Market
    price: float
    change: float | None = None
    change_percent: float | None = None
    bid: float | None = None
    ask: float | None = None
    volume: int = 0
    timestamp: datetime


class OptionContract(BaseModel):
    """Single option contract."""

    symbol: str
    underlying: str
    strike: float
    expiration: date
    option_type: OptionType
    bid: float | None = None
    ask: float | None = None
    last_price: float | None = None
    volume: int = 0
    open_interest: int = 0
    implied_volatility: float | None = None
    greeks: Greeks | None = None


class OptionChain(BaseModel):
    """Option chain for a symbol."""

    underlying: str
    market: Market
    expirations: list[date]
    calls: list[OptionContract]
    puts: list[OptionContract]
    timestamp: datetime


class VolatilitySurface(BaseModel):
    """Implied volatility surface."""

    symbol: str
    market: Market
    strikes: list[float]
    expirations: list[date]
    call_ivs: list[list[float]]  # 2D grid [expiration][strike]
    put_ivs: list[list[float]]  # 2D grid [expiration][strike]
    timestamp: datetime


class MarketInfo(BaseModel):
    """Market information."""

    code: Market
    name: str
    currency: str
    timezone: str
    trading_hours: str
    is_open: bool = False


class WatchlistItem(BaseModel):
    """Watchlist entry."""

    symbol: str
    market: Market
    name: str | None = None
    added_at: datetime


class PriceBar(BaseModel):
    """OHLCV price bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class PriceHistory(BaseModel):
    """Historical price data."""

    symbol: str
    market: Market
    interval: str  # "1d", "1h", "5m", etc.
    bars: list[PriceBar]


# Dashboard Models

class IVAnalysis(BaseModel):
    """IV Rank and Percentile analysis."""

    symbol: str
    market: Market
    current_iv: float = Field(description="Current ATM implied volatility")
    iv_rank: float = Field(description="IV rank (0-100) within 52-week range")
    iv_percentile: float = Field(description="Percentage of days with lower IV")
    iv_52w_high: float = Field(description="52-week high IV")
    iv_52w_low: float = Field(description="52-week low IV")
    iv_30d_avg: float = Field(description="30-day average IV")
    timestamp: datetime


Sentiment = Literal["bearish", "slightly_bearish", "neutral", "slightly_bullish", "bullish"]


class MarketSentiment(BaseModel):
    """Put/Call ratio and sentiment indicators."""

    symbol: str
    market: Market
    put_call_ratio: float = Field(description="Put volume / Call volume ratio")
    total_call_volume: int
    total_put_volume: int
    call_open_interest: int
    put_open_interest: int
    sentiment: Sentiment
    timestamp: datetime


AlertType = Literal["volume_spike", "unusual_pc_ratio", "oi_change"]


class UnusualActivityAlert(BaseModel):
    """Single unusual activity alert."""

    symbol: str
    market: Market
    alert_type: AlertType
    description: str
    significance: float = Field(description="Significance score 1-10")
    details: dict = Field(default_factory=dict)
    timestamp: datetime


class UnusualActivityResponse(BaseModel):
    """List of unusual activity alerts."""

    alerts: list[UnusualActivityAlert]


class StrategySuggestion(BaseModel):
    """Single strategy recommendation."""

    strategy: str = Field(description="Strategy identifier (e.g., 'iron_condor')")
    display_name: str = Field(description="Human-readable name")
    suitability: float = Field(description="Suitability score 0-100")
    reasoning: str = Field(description="Why this strategy is suggested")
    risk_level: str = Field(default="medium", description="low, medium, high")
    max_profit: str | None = None
    max_loss: str | None = None


class MarketConditions(BaseModel):
    """Current market conditions for strategy suggestions."""

    vix_level: str = Field(description="low, normal, elevated, high")
    iv_rank: str = Field(description="low, medium, high")
    trend: str = Field(description="bullish, slightly_bullish, neutral, slightly_bearish, bearish")
    volatility_outlook: str = Field(description="increasing, stable, decreasing")


class StrategySuggestionsResponse(BaseModel):
    """Strategy suggestions based on market conditions."""

    symbol: str
    market: Market
    market_conditions: MarketConditions
    suggestions: list[StrategySuggestion]
    timestamp: datetime


# ============================================================
# ADVANCED TRADING FEATURES
# ============================================================

# Payoff Diagram Models
ActionType = Literal["buy", "sell"]


class PayoffLeg(BaseModel):
    """Single leg for payoff calculation."""

    option_type: OptionType
    action: ActionType
    strike: float
    quantity: int = 1
    premium: float = Field(description="Premium per contract")
    expiration: date | None = None


class PayoffPoint(BaseModel):
    """P/L at a specific price point."""

    price: float
    pnl: float
    leg_pnls: list[float] = Field(default_factory=list)


class PayoffResult(BaseModel):
    """Result of payoff calculation."""

    underlying_price: float
    legs: list[PayoffLeg]
    points: list[PayoffPoint]
    breakevens: list[float]
    max_profit: float | None = None
    max_loss: float | None = None
    net_premium: float = Field(description="Net credit (+) or debit (-)")


# Position Tracking Models
PositionStatus = Literal["open", "closed"]


class PositionLeg(BaseModel):
    """Leg within a position."""

    option_type: OptionType
    action: ActionType
    strike: float
    expiration: date
    quantity: int
    entry_premium: float
    current_premium: float | None = None


class Position(BaseModel):
    """Tracked position."""

    id: str
    symbol: str
    market: Market
    strategy_name: str = "Custom"
    legs: list[PositionLeg]
    entry_date: datetime
    entry_cost: float = Field(description="Total cost/credit to open")
    current_value: float | None = None
    pnl: float | None = None
    pnl_percent: float | None = None
    status: PositionStatus = "open"
    notes: str = ""
    greeks: Greeks | None = None


class PortfolioSummary(BaseModel):
    """Aggregated portfolio summary."""

    total_positions: int
    open_positions: int
    total_value: float
    total_pnl: float
    total_pnl_percent: float
    aggregate_delta: float
    aggregate_gamma: float
    aggregate_theta: float
    aggregate_vega: float


# Options Scanner Models
class ScanCriteria(BaseModel):
    """Criteria for options scanner."""

    market: Market = "US"
    symbols: list[str] | None = None
    iv_rank_min: float | None = None
    iv_rank_max: float | None = None
    volume_min: int | None = None
    open_interest_min: int | None = None
    dte_min: int | None = None
    dte_max: int | None = None
    delta_min: float | None = None
    delta_max: float | None = None


class ScanResult(BaseModel):
    """Single scanner result."""

    symbol: str
    market: Market
    price: float
    iv_rank: float
    iv_percentile: float
    put_call_ratio: float
    total_volume: int
    total_open_interest: int
    sentiment: Sentiment
    score: float = Field(description="Composite score 0-100")


class ScanResponse(BaseModel):
    """Scanner response."""

    criteria: ScanCriteria
    results: list[ScanResult]
    total_scanned: int
    timestamp: datetime


# Paper Trading Models
OrderType = Literal["market", "limit"]
OrderSide = Literal["buy", "sell"]
OrderStatus = Literal["pending", "filled", "cancelled", "rejected"]


class PaperOrder(BaseModel):
    """Paper trading order."""

    id: str
    account_id: str
    symbol: str
    market: Market
    option_symbol: str | None = None
    order_type: OrderType
    side: OrderSide
    quantity: int
    limit_price: float | None = None
    status: OrderStatus = "pending"
    filled_price: float | None = None
    filled_quantity: int = 0
    created_at: datetime
    filled_at: datetime | None = None


class PaperPosition(BaseModel):
    """Paper trading position."""

    symbol: str
    market: Market
    option_symbol: str | None = None
    quantity: int
    avg_entry_price: float
    current_price: float | None = None
    unrealized_pnl: float = 0
    realized_pnl: float = 0


class PaperAccount(BaseModel):
    """Paper trading account."""

    id: str
    name: str = "Default"
    initial_cash: float = 100000.0
    cash: float = 100000.0
    positions: list[PaperPosition] = Field(default_factory=list)
    orders: list[PaperOrder] = Field(default_factory=list)
    total_value: float = 100000.0
    total_pnl: float = 0
    total_pnl_percent: float = 0
    created_at: datetime
    last_updated: datetime


# Trade Journal Models
TradeStatus = Literal["open", "closed", "cancelled"]


class TradeEntry(BaseModel):
    """Trade journal entry."""

    id: str
    symbol: str
    market: Market
    strategy: str = "Custom"
    entry_date: datetime
    entry_price: float
    quantity: int
    exit_date: datetime | None = None
    exit_price: float | None = None
    pnl: float | None = None
    pnl_percent: float | None = None
    status: TradeStatus = "open"
    notes: str = ""
    tags: list[str] = Field(default_factory=list)
    lessons: str = ""


class TradeStats(BaseModel):
    """Trade journal statistics."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    total_pnl: float
    avg_pnl: float
    best_trade: float
    worst_trade: float
    avg_holding_days: float


# Alert System Models
AlertRuleType = Literal["price_above", "price_below", "iv_rank_above", "iv_rank_below", "volume_above", "pc_ratio_above", "pc_ratio_below"]
AlertSeverity = Literal["info", "warning", "critical"]


class AlertRule(BaseModel):
    """Alert rule configuration."""

    id: str
    symbol: str
    market: Market
    rule_type: AlertRuleType
    threshold: float
    enabled: bool = True
    created_at: datetime
    last_triggered: datetime | None = None
    trigger_count: int = 0


class AlertNotification(BaseModel):
    """Triggered alert notification."""

    id: str
    rule_id: str
    symbol: str
    market: Market
    message: str
    severity: AlertSeverity = "info"
    current_value: float
    threshold: float
    triggered_at: datetime
    acknowledged: bool = False


# IV History Model
class IVHistoryPoint(BaseModel):
    """Historical IV data point."""

    date: date
    iv: float
    iv_rank: float
    iv_percentile: float
    price: float


class IVHistory(BaseModel):
    """Historical IV data."""

    symbol: str
    market: Market
    data: list[IVHistoryPoint]


# Earnings Calendar Model
class EarningsEvent(BaseModel):
    """Earnings calendar event."""

    symbol: str
    market: Market
    earnings_date: date
    time_of_day: Literal["before_open", "after_close", "unknown"] = "unknown"
    estimated_eps: float | None = None
    actual_eps: float | None = None
    iv_before: float | None = None
    iv_after: float | None = None
    iv_crush_percent: float | None = None
    price_move_percent: float | None = None


class EarningsCalendar(BaseModel):
    """Earnings calendar response."""

    events: list[EarningsEvent]
    start_date: date
    end_date: date


# Probability Calculator Models
class ProbabilityResult(BaseModel):
    """Probability calculation result."""

    symbol: str
    current_price: float
    strike: float
    days_to_expiration: int
    iv: float
    probability_itm: float
    probability_otm: float
    probability_profit: float
    expected_move: float
    one_std_range: tuple[float, float]
    two_std_range: tuple[float, float]


# Correlation Matrix Model
class CorrelationEntry(BaseModel):
    """Correlation between two symbols."""

    symbol1: str
    symbol2: str
    correlation: float


class CorrelationMatrix(BaseModel):
    """Correlation matrix for portfolio."""

    symbols: list[str]
    matrix: list[list[float]]
    period_days: int = 30


# Stress Testing Models
class StressScenario(BaseModel):
    """Stress test scenario."""

    name: str
    price_change_percent: float
    iv_change_percent: float
    description: str = ""


class StressTestResult(BaseModel):
    """Stress test result for a position."""

    position_id: str
    symbol: str
    scenario: StressScenario
    current_value: float
    stressed_value: float
    pnl_impact: float
    pnl_impact_percent: float


class PortfolioStressTest(BaseModel):
    """Portfolio-wide stress test."""

    scenario: StressScenario
    results: list[StressTestResult]
    total_current_value: float
    total_stressed_value: float
    total_pnl_impact: float
    total_pnl_impact_percent: float


# ============================================================
# JPM VOLATILITY RESEARCH MODELS
# ============================================================

JPMStrategyType = Literal["call_overwriting", "call_buying", "put_underwriting", "put_buying"]
JPMScreenType = Literal["rich_iv", "cheap_iv", "iv_top_movers", "iv_bottom_movers", "range_bound", "trending"]


class JPMTradingCandidate(BaseModel):
    """JPM options trading candidate."""

    ticker: str
    strategy: JPMStrategyType
    iv30: float = Field(description="30-day implied volatility")
    iv_percentile: float = Field(description="IV percentile rank")
    hv30: float | None = Field(default=None, description="30-day historical volatility")
    iv_hv_spread: float | None = Field(default=None, description="IV minus HV spread")
    skew: float | None = Field(default=None, description="Put/Call IV skew")
    rationale: str = Field(description="Why this is a candidate")


class JPMVolatilityScreen(BaseModel):
    """JPM volatility screen result."""

    ticker: str
    screen_type: JPMScreenType
    iv30: float
    iv60: float | None = None
    iv90: float | None = None
    iv_percentile: float
    iv_change_1w: float | None = Field(default=None, description="1-week IV change %")
    iv_change_1m: float | None = Field(default=None, description="1-month IV change %")
    hv30: float | None = None
    price: float | None = None
    price_change_1m: float | None = None


class JPMStockData(BaseModel):
    """Full JPM stock data row."""

    ticker: str
    price: float | None = None
    price_change_1d: float | None = None
    price_change_1m: float | None = None
    iv30: float
    iv60: float | None = None
    iv90: float | None = None
    iv_percentile: float
    iv_rank: float | None = None
    hv30: float | None = None
    hv60: float | None = None
    iv_hv_spread: float | None = None
    skew: float | None = Field(default=None, description="25-delta put/call skew")
    put_skew: float | None = None
    call_skew: float | None = None
    term_structure: Literal["contango", "backwardation", "flat"] | None = None
    sector: str | None = None


class JPMReportMetadata(BaseModel):
    """JPM report metadata."""

    report_date: date
    report_title: str = "US Single Stock Volatility Chartbook"
    source: str = "J.P. Morgan"
    total_stocks: int
    last_updated: datetime


class JPMResearchData(BaseModel):
    """Complete JPM research data."""

    metadata: JPMReportMetadata
    call_overwriting: list[JPMTradingCandidate]
    call_buying: list[JPMTradingCandidate]
    put_underwriting: list[JPMTradingCandidate]
    put_buying: list[JPMTradingCandidate]
    rich_iv: list[JPMVolatilityScreen]
    cheap_iv: list[JPMVolatilityScreen]
    iv_top_movers: list[JPMVolatilityScreen]
    iv_bottom_movers: list[JPMVolatilityScreen]
    all_stocks: list[JPMStockData]


# ============================================================
# MARKET INDICATORS MODELS
# ============================================================


class BondRatesData(BaseModel):
    """Bond and interest rate data."""

    tnx_yield: float = Field(description="10-Year Treasury Yield")
    irx_yield: float = Field(description="2-Year Treasury Yield proxy")
    yield_spread: float = Field(description="10Y-2Y yield spread")
    tlt_price: float = Field(description="TLT 20+ Year Treasury ETF price")
    tlt_change: float | None = None
    tlt_change_percent: float | None = None
    timestamp: datetime


class CommoditiesData(BaseModel):
    """Commodity indicators."""

    gold_price: float = Field(description="GLD gold ETF price")
    gold_change: float | None = None
    gold_change_percent: float | None = None
    oil_price: float = Field(description="USO oil ETF price")
    oil_change: float | None = None
    oil_change_percent: float | None = None
    dollar_price: float = Field(description="UUP dollar ETF price")
    dollar_change: float | None = None
    dollar_change_percent: float | None = None
    timestamp: datetime


class SectorData(BaseModel):
    """Single sector ETF data."""

    symbol: str
    name: str
    price: float
    change: float | None = None
    change_percent: float | None = None


class MarketBreadthData(BaseModel):
    """Market breadth indicators."""

    advances: int = Field(description="Number of advancing issues")
    declines: int = Field(description="Number of declining issues")
    advance_decline_ratio: float = Field(description="Advances / Declines ratio")
    new_highs: int = Field(description="Number of new 52-week highs")
    new_lows: int = Field(description="Number of new 52-week lows")
    highs_lows_ratio: float = Field(description="New Highs / New Lows ratio")
    mcclellan_oscillator: float | None = Field(default=None, description="McClellan Oscillator value")
    timestamp: datetime


class MarketIndicatorsResponse(BaseModel):
    """Complete market indicators response."""

    bonds: BondRatesData
    commodities: CommoditiesData
    sectors: list[SectorData]
    breadth: MarketBreadthData
    timestamp: datetime
