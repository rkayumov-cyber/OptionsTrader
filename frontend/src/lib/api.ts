import axios from "axios"

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

export type Market = "US" | "JP" | "HK"

export interface Quote {
  symbol: string
  market: Market
  price: number
  change: number | null
  change_percent: number | null
  bid: number | null
  ask: number | null
  volume: number
  timestamp: string
}

export interface Greeks {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
}

export interface OptionContract {
  symbol: string
  underlying: string
  strike: number
  expiration: string
  option_type: "call" | "put"
  bid: number | null
  ask: number | null
  last_price: number | null
  volume: number
  open_interest: number
  implied_volatility: number | null
  greeks: Greeks | null
}

export interface OptionChain {
  underlying: string
  market: Market
  expirations: string[]
  calls: OptionContract[]
  puts: OptionContract[]
  timestamp: string
}

export interface VolatilitySurface {
  symbol: string
  market: Market
  strikes: number[]
  expirations: string[]
  call_ivs: number[][]
  put_ivs: number[][]
  timestamp: string
}

export interface WatchlistItem {
  symbol: string
  market: Market
  name: string | null
  added_at: string
}

export interface PriceBar {
  timestamp: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface PriceHistory {
  symbol: string
  market: Market
  interval: string
  bars: PriceBar[]
}

export interface Provider {
  name: string
  markets: Market[]
  active: boolean
}

// API functions
export async function getQuote(symbol: string, market: Market): Promise<Quote> {
  const { data } = await api.get(`/api/quote/${symbol}`, { params: { market } })
  return data
}

export interface BatchSymbol {
  symbol: string
  market: Market
}

export async function getBatchQuotes(
  symbols: BatchSymbol[]
): Promise<Record<string, Quote>> {
  const { data } = await api.post("/api/quotes/batch", { symbols })
  return data
}

export async function getBatchIVAnalysis(
  symbols: BatchSymbol[]
): Promise<Record<string, IVAnalysis>> {
  const { data } = await api.post("/api/iv-analysis/batch", { symbols })
  return data
}

export async function getOptionChain(
  symbol: string,
  market: Market,
  expiration?: string
): Promise<OptionChain> {
  const { data } = await api.get(`/api/options/${symbol}`, {
    params: { market, expiration },
  })
  return data
}

export async function getVolatilitySurface(
  symbol: string,
  market: Market
): Promise<VolatilitySurface> {
  const { data } = await api.get(`/api/volatility/${symbol}`, { params: { market } })
  return data
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const { data } = await api.get("/api/watchlist")
  return data
}

export async function addToWatchlist(
  symbol: string,
  market: Market,
  name?: string
): Promise<void> {
  await api.post("/api/watchlist", { symbol, market, name })
}

export async function removeFromWatchlist(
  symbol: string,
  market: Market
): Promise<void> {
  await api.delete(`/api/watchlist/${symbol}`, { params: { market } })
}

export async function getProviders(): Promise<{ active: string; available: Provider[] }> {
  const { data } = await api.get("/api/providers")
  return data
}

export interface SwitchProviderRequest {
  provider: string
  host?: string
  port?: number
  client_id?: number
  access_token?: string
  environment?: string
}

export async function switchProvider(request: SwitchProviderRequest): Promise<void> {
  await api.post("/api/providers/switch", request)
}

export async function getMarkets(): Promise<Record<Market, { name: string; currency: string }>> {
  const { data } = await api.get("/api/markets")
  return data
}

export async function getPriceHistory(
  symbol: string,
  market: Market,
  interval: string = "1d",
  limit: number = 30
): Promise<PriceHistory> {
  const { data } = await api.get(`/api/history/${symbol}`, {
    params: { market, interval, limit },
  })
  return data
}

// Dashboard types

export interface IVAnalysis {
  symbol: string
  market: Market
  current_iv: number
  iv_rank: number
  iv_percentile: number
  iv_52w_high: number
  iv_52w_low: number
  iv_30d_avg: number
  timestamp: string
}

export type Sentiment = "bearish" | "slightly_bearish" | "neutral" | "slightly_bullish" | "bullish"

export interface MarketSentiment {
  symbol: string
  market: Market
  put_call_ratio: number
  total_call_volume: number
  total_put_volume: number
  call_open_interest: number
  put_open_interest: number
  sentiment: Sentiment
  timestamp: string
}

export type AlertType = "volume_spike" | "unusual_pc_ratio" | "oi_change"

export interface UnusualActivityAlert {
  symbol: string
  market: Market
  alert_type: AlertType
  description: string
  significance: number
  details: Record<string, unknown>
  timestamp: string
}

export interface UnusualActivityResponse {
  alerts: UnusualActivityAlert[]
}

export interface StrategySuggestion {
  strategy: string
  display_name: string
  suitability: number
  reasoning: string
  risk_level: string
  max_profit: string | null
  max_loss: string | null
}

export interface MarketConditions {
  vix_level: string
  iv_rank: string
  trend: string
  volatility_outlook: string
}

export interface StrategySuggestionsResponse {
  symbol: string
  market: Market
  market_conditions: MarketConditions
  suggestions: StrategySuggestion[]
  timestamp: string
}

// Dashboard API functions

export async function getIVAnalysis(symbol: string, market: Market): Promise<IVAnalysis> {
  const { data } = await api.get(`/api/iv-analysis/${symbol}`, { params: { market } })
  return data
}

export async function getMarketSentiment(symbol: string, market: Market): Promise<MarketSentiment> {
  const { data } = await api.get(`/api/market-sentiment/${symbol}`, { params: { market } })
  return data
}

export async function getUnusualActivity(market?: Market): Promise<UnusualActivityResponse> {
  const { data } = await api.get("/api/unusual-activity", { params: market ? { market } : {} })
  return data
}

export async function getStrategySuggestions(
  symbol: string,
  market: Market
): Promise<StrategySuggestionsResponse> {
  const { data } = await api.get(`/api/strategy-suggestions/${symbol}`, { params: { market } })
  return data
}

// =============================================================================
// PAYOFF DIAGRAM TYPES & API
// =============================================================================

export type OptionType = "call" | "put"
export type ActionType = "buy" | "sell"

export interface PayoffLeg {
  option_type: OptionType
  action: ActionType
  strike: float
  quantity: number
  premium: number
}

export interface PayoffPoint {
  price: number
  pnl: number
}

export interface PayoffResult {
  legs: PayoffLeg[]
  underlying_price: number
  points: PayoffPoint[]
  breakevens: number[]
  max_profit: number | null
  max_loss: number | null
  net_premium: number
}

export interface PayoffRequest {
  legs: PayoffLeg[]
  underlying_price: number
  price_range_percent?: number
  num_points?: number
}

export async function calculatePayoff(request: PayoffRequest): Promise<PayoffResult> {
  const { data } = await api.post("/api/payoff/calculate", request)
  return data
}

export async function getPayoffTemplate(
  strategy: string,
  underlyingPrice: number
): Promise<PayoffLeg[]> {
  const { data } = await api.get(`/api/payoff/templates/${strategy}`, {
    params: { underlying_price: underlyingPrice },
  })
  return data
}

export async function getPayoffStrategies(): Promise<string[]> {
  const { data } = await api.get("/api/payoff/strategies")
  return data
}

// Time Series Payoff (Theta Decay Visualization)
export interface TimeCurvePoint {
  price: number
  pnl: number
}

export interface TimeCurve {
  dte: number
  label: string
  points: TimeCurvePoint[]
  breakevens: number[]
}

export interface TimeSeriesPayoffResult {
  underlying_price: number
  legs: PayoffLeg[]
  time_curves: TimeCurve[]
  max_dte: number
  iv: number
  rate: number
  max_profit: number | null
  max_loss: number | null
  net_premium: number
  expiration_breakevens: number[]
}

export interface TimeSeriesPayoffRequest {
  legs: PayoffLeg[]
  underlying_price: number
  max_dte?: number
  iv?: number
  rate?: number
  price_range_percent?: number
  num_points?: number
  time_intervals?: number[]
}

export async function calculateTimeSeriesPayoff(
  request: TimeSeriesPayoffRequest
): Promise<TimeSeriesPayoffResult> {
  const { data } = await api.post("/api/payoff/time-series", request)
  return data
}

// =============================================================================
// POSITION TRACKER TYPES & API
// =============================================================================

export type PositionStatus = "open" | "closed" | "expired"

export interface PositionLeg {
  option_type: OptionType
  action: ActionType
  strike: number
  expiration: string
  quantity: number
  entry_premium: number
  current_premium: number
  option_symbol?: string
}

export interface PositionGreeks {
  delta: number
  gamma: number
  theta: number
  vega: number
}

export interface Position {
  id: string
  symbol: string
  market: Market
  strategy_name: string
  legs: PositionLeg[]
  entry_date: string
  entry_cost: number
  current_value: number
  unrealized_pnl: number
  realized_pnl: number
  status: PositionStatus
  greeks?: PositionGreeks
  notes?: string
  tags: string[]
  closed_at?: string
}

export interface PortfolioSummary {
  total_positions: number
  open_positions: number
  total_value: number
  total_unrealized_pnl: number
  total_realized_pnl: number
  total_pnl: number
  aggregate_greeks: PositionGreeks
  positions_by_market: Record<Market, number>
  positions_by_status: Record<PositionStatus, number>
}

export interface CreatePositionRequest {
  symbol: string
  market: Market
  strategy_name?: string
  legs: Omit<PositionLeg, "current_premium">[]
  notes?: string
  tags?: string[]
}

export async function getPositions(): Promise<Position[]> {
  const { data } = await api.get("/api/positions")
  return data
}

export async function getPosition(id: string): Promise<Position> {
  const { data } = await api.get(`/api/positions/${id}`)
  return data
}

export async function createPosition(request: CreatePositionRequest): Promise<Position> {
  const { data } = await api.post("/api/positions", request)
  return data
}

export async function updatePosition(
  id: string,
  updates: Partial<Position>
): Promise<Position> {
  const { data } = await api.put(`/api/positions/${id}`, updates)
  return data
}

export async function deletePosition(id: string): Promise<void> {
  await api.delete(`/api/positions/${id}`)
}

export async function closePosition(
  id: string,
  exitPremiums: Record<string, number>
): Promise<Position> {
  const { data } = await api.post(`/api/positions/${id}/close`, {
    exit_premiums: exitPremiums,
  })
  return data
}

export async function getPortfolioSummary(): Promise<PortfolioSummary> {
  const { data } = await api.get("/api/positions/summary")
  return data
}

// =============================================================================
// OPTIONS SCANNER TYPES & API
// =============================================================================

export interface ScanCriteria {
  market: Market
  symbols?: string[]
  iv_rank_min?: number
  iv_rank_max?: number
  volume_min?: number
  open_interest_min?: number
  price_min?: number
  price_max?: number
  dte_min?: number
  dte_max?: number
}

export interface ScanResult {
  symbol: string
  market: Market
  price: number
  iv_rank: number
  iv_percentile: number
  put_call_ratio: number
  total_volume: number
  total_open_interest: number
  sentiment: Sentiment
  score: number
}

export interface ScanResponse {
  criteria: ScanCriteria
  results: ScanResult[]
  total_scanned: number
  timestamp: string
}

export async function scanOptions(criteria: ScanCriteria): Promise<ScanResponse> {
  const { data } = await api.post("/api/scanner/scan", criteria)
  return data
}

export async function getHighIVOpportunities(market: Market = "US"): Promise<ScanResponse> {
  const { data } = await api.get("/api/scanner/high-iv", { params: { market } })
  return data
}

export async function getLowIVOpportunities(market: Market = "US"): Promise<ScanResponse> {
  const { data } = await api.get("/api/scanner/low-iv", { params: { market } })
  return data
}

export async function getHighVolumeActivity(market: Market = "US"): Promise<ScanResponse> {
  const { data } = await api.get("/api/scanner/high-volume", { params: { market } })
  return data
}

// =============================================================================
// PAPER TRADING TYPES & API
// =============================================================================

export type OrderType = "market" | "limit" | "stop" | "stop_limit"
export type OrderSide = "buy" | "sell"
export type OrderStatus = "pending" | "filled" | "cancelled" | "rejected" | "expired"

export interface PaperPosition {
  symbol: string
  market: Market
  option_symbol?: string
  quantity: number
  avg_entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
}

export interface PaperOrder {
  id: string
  account_id: string
  symbol: string
  market: Market
  option_symbol?: string
  order_type: OrderType
  side: OrderSide
  quantity: number
  limit_price?: number
  stop_price?: number
  status: OrderStatus
  filled_price?: number
  filled_quantity?: number
  created_at: string
  filled_at?: string
}

export interface PaperAccount {
  id: string
  name: string
  initial_cash: number
  cash: number
  total_value: number
  total_pnl: number
  total_pnl_percent: number
  positions: PaperPosition[]
  orders: PaperOrder[]
  created_at: string
  last_updated: string
}

export interface CreatePaperAccountRequest {
  name?: string
  initial_cash?: number
}

export interface PlaceOrderRequest {
  account_id: string
  symbol: string
  market: Market
  side: OrderSide
  quantity: number
  order_type?: OrderType
  limit_price?: number
  option_symbol?: string
}

export async function createPaperAccount(
  request?: CreatePaperAccountRequest
): Promise<PaperAccount> {
  const { data } = await api.post("/api/paper/accounts", request || {})
  return data
}

export async function getPaperAccount(accountId: string): Promise<PaperAccount> {
  const { data } = await api.get(`/api/paper/accounts/${accountId}`)
  return data
}

export async function getDefaultPaperAccount(): Promise<PaperAccount> {
  const { data } = await api.get("/api/paper/accounts/default")
  return data
}

export async function getAllPaperAccounts(): Promise<PaperAccount[]> {
  const { data } = await api.get("/api/paper/accounts")
  return data
}

export async function placePaperOrder(request: PlaceOrderRequest): Promise<PaperOrder> {
  const { data } = await api.post("/api/paper/orders", request)
  return data
}

export async function getPaperOrders(accountId: string): Promise<PaperOrder[]> {
  const { data } = await api.get(`/api/paper/accounts/${accountId}/orders`)
  return data
}

export async function getPaperPositions(accountId: string): Promise<PaperPosition[]> {
  const { data } = await api.get(`/api/paper/accounts/${accountId}/positions`)
  return data
}

export async function cancelPaperOrder(
  accountId: string,
  orderId: string
): Promise<{ success: boolean }> {
  const { data } = await api.delete(`/api/paper/accounts/${accountId}/orders/${orderId}`)
  return data
}

export async function resetPaperAccount(accountId: string): Promise<PaperAccount> {
  const { data } = await api.post(`/api/paper/accounts/${accountId}/reset`)
  return data
}

// =============================================================================
// TRADE JOURNAL TYPES & API
// =============================================================================

export type TradeStatus = "open" | "closed"

export interface TradeEntry {
  id: string
  symbol: string
  market: Market
  strategy: string
  entry_date: string
  exit_date?: string
  entry_price: number
  exit_price?: number
  quantity: number
  pnl?: number
  pnl_percent?: number
  status: TradeStatus
  notes: string
  lessons: string
  tags: string[]
}

export interface TradeStats {
  total_trades: number
  winning_trades: number
  losing_trades: number
  win_rate: number
  avg_win: number
  avg_loss: number
  profit_factor: number
  total_pnl: number
  avg_pnl: number
  best_trade: number
  worst_trade: number
  avg_holding_days: number
}

export interface CreateTradeRequest {
  symbol: string
  market: Market
  entry_price: number
  quantity: number
  strategy?: string
  notes?: string
  tags?: string[]
}

export interface CloseTradeRequest {
  exit_price: number
  notes?: string
  lessons?: string
}

export async function getJournalTrades(): Promise<TradeEntry[]> {
  const { data } = await api.get("/api/journal/trades")
  return data
}

export async function getJournalTrade(id: string): Promise<TradeEntry> {
  const { data } = await api.get(`/api/journal/trades/${id}`)
  return data
}

export async function createJournalTrade(request: CreateTradeRequest): Promise<TradeEntry> {
  const { data } = await api.post("/api/journal/trades", request)
  return data
}

export async function updateJournalTrade(
  id: string,
  updates: Partial<TradeEntry>
): Promise<TradeEntry> {
  const { data } = await api.put(`/api/journal/trades/${id}`, updates)
  return data
}

export async function closeJournalTrade(
  id: string,
  request: CloseTradeRequest
): Promise<TradeEntry> {
  const { data } = await api.post(`/api/journal/trades/${id}/close`, request)
  return data
}

export async function deleteJournalTrade(id: string): Promise<void> {
  await api.delete(`/api/journal/trades/${id}`)
}

export async function getJournalStats(): Promise<TradeStats> {
  const { data } = await api.get("/api/journal/stats")
  return data
}

export async function getTradesBySymbol(symbol: string): Promise<TradeEntry[]> {
  const { data } = await api.get(`/api/journal/trades/symbol/${symbol}`)
  return data
}

export async function getTradesByStrategy(strategy: string): Promise<TradeEntry[]> {
  const { data } = await api.get(`/api/journal/trades/strategy/${strategy}`)
  return data
}

// =============================================================================
// ALERTS SYSTEM TYPES & API
// =============================================================================

export type AlertRuleType =
  | "price_above"
  | "price_below"
  | "iv_rank_above"
  | "iv_rank_below"
  | "volume_above"
  | "pc_ratio_above"
  | "pc_ratio_below"

export type AlertSeverity = "info" | "warning" | "critical"

export interface AlertRule {
  id: string
  symbol: string
  market: Market
  rule_type: AlertRuleType
  threshold: number
  enabled: boolean
  created_at: string
  last_triggered?: string
  trigger_count: number
}

export interface AlertNotification {
  id: string
  rule_id: string
  symbol: string
  market: Market
  message: string
  severity: AlertSeverity
  current_value: number
  threshold: number
  triggered_at: string
  acknowledged: boolean
}

export interface CreateAlertRuleRequest {
  symbol: string
  market: Market
  rule_type: AlertRuleType
  threshold: number
}

export async function getAlertRules(): Promise<AlertRule[]> {
  const { data } = await api.get("/api/alerts/rules")
  return data
}

export async function getAlertRule(id: string): Promise<AlertRule> {
  const { data } = await api.get(`/api/alerts/rules/${id}`)
  return data
}

export async function createAlertRule(request: CreateAlertRuleRequest): Promise<AlertRule> {
  const { data } = await api.post("/api/alerts/rules", request)
  return data
}

export async function updateAlertRule(
  id: string,
  updates: Partial<AlertRule>
): Promise<AlertRule> {
  const { data } = await api.put(`/api/alerts/rules/${id}`, updates)
  return data
}

export async function deleteAlertRule(id: string): Promise<void> {
  await api.delete(`/api/alerts/rules/${id}`)
}

export async function toggleAlertRule(id: string): Promise<AlertRule> {
  const { data } = await api.post(`/api/alerts/rules/${id}/toggle`)
  return data
}

export async function getAlertNotifications(): Promise<AlertNotification[]> {
  const { data } = await api.get("/api/alerts/notifications")
  return data
}

export async function getUnacknowledgedAlerts(): Promise<AlertNotification[]> {
  const { data } = await api.get("/api/alerts/notifications/unacknowledged")
  return data
}

export async function acknowledgeAlert(id: string): Promise<{ success: boolean }> {
  const { data } = await api.post(`/api/alerts/notifications/${id}/acknowledge`)
  return data
}

export async function acknowledgeAllAlerts(): Promise<{ count: number }> {
  const { data } = await api.post("/api/alerts/notifications/acknowledge-all")
  return data
}

export async function deleteAlertNotification(id: string): Promise<void> {
  await api.delete(`/api/alerts/notifications/${id}`)
}

export async function checkAlerts(
  marketData: Record<string, Record<string, number>>
): Promise<AlertNotification[]> {
  const { data } = await api.post("/api/alerts/check", { market_data: marketData })
  return data
}

// =============================================================================
// ANALYTICS TYPES & API
// =============================================================================

// Probability Calculator
export interface ProbabilityResult {
  symbol: string
  current_price: number
  strike: number
  dte: number
  iv: number
  probability_above: number
  probability_below: number
  probability_between?: number
  strike_upper?: number
  strike_lower?: number
  expected_move: number
  one_std_range: [number, number]
  two_std_range: [number, number]
}

export async function calculateProbability(
  symbol: string,
  market: Market,
  strike: number,
  dte: number,
  iv: number,
  strikeLower?: number,
  strikeUpper?: number
): Promise<ProbabilityResult> {
  const { data } = await api.get("/api/probability/calculate", {
    params: {
      symbol,
      market,
      strike,
      dte,
      iv,
      strike_lower: strikeLower,
      strike_upper: strikeUpper,
    },
  })
  return data
}

// IV History
export interface IVHistoryPoint {
  date: string
  iv: number
  iv_rank: number
  price: number
}

export interface IVHistoryResponse {
  symbol: string
  market: Market
  history: IVHistoryPoint[]
  current_iv: number
  current_iv_rank: number
  iv_52w_high: number
  iv_52w_low: number
}

export async function getIVHistory(
  symbol: string,
  market: Market,
  days: number = 90
): Promise<IVHistoryResponse> {
  const { data } = await api.get(`/api/iv-history/${symbol}`, {
    params: { market, days },
  })
  return data
}

// Term Structure
export interface TermStructurePoint {
  expiration: string
  dte: number
  iv: number
  call_iv: number
  put_iv: number
}

export interface TermStructureResponse {
  symbol: string
  market: Market
  structure: TermStructurePoint[]
  contango: boolean
  timestamp: string
}

export async function getTermStructure(
  symbol: string,
  market: Market
): Promise<TermStructureResponse> {
  const { data } = await api.get(`/api/term-structure/${symbol}`, {
    params: { market },
  })
  return data
}

// Skew Analysis
export interface SkewPoint {
  strike: number
  moneyness: number
  call_iv: number
  put_iv: number
  skew: number
}

export interface SkewResponse {
  symbol: string
  market: Market
  expiration: string
  underlying_price: number
  skew_data: SkewPoint[]
  put_skew_index: number
  call_skew_index: number
  timestamp: string
}

export async function getSkewAnalysis(
  symbol: string,
  market: Market,
  expiration?: string
): Promise<SkewResponse> {
  const { data } = await api.get(`/api/skew/${symbol}`, {
    params: { market, expiration },
  })
  return data
}

// =============================================================================
// RISK MANAGEMENT TYPES & API
// =============================================================================

// Earnings Calendar
export interface EarningsEvent {
  symbol: string
  market: Market
  company_name: string
  earnings_date: string
  time_of_day: "before_open" | "after_close" | "during_market" | "unknown"
  estimated_eps?: number
  actual_eps?: number
  surprise_percent?: number
  iv_before?: number
  iv_after?: number
  iv_crush_percent?: number
}

export interface EarningsCalendarResponse {
  events: EarningsEvent[]
  start_date: string
  end_date: string
}

export async function getEarningsCalendar(
  symbols?: string[],
  days: number = 30
): Promise<EarningsCalendarResponse> {
  const { data } = await api.get("/api/earnings", {
    params: { symbols: symbols?.join(","), days },
  })
  return data
}

// Correlation Matrix
export interface CorrelationPair {
  symbol1: string
  symbol2: string
  correlation: number
}

export interface CorrelationMatrixResponse {
  symbols: string[]
  matrix: number[][]
  pairs: CorrelationPair[]
  period_days: number
  timestamp: string
}

export async function getCorrelationMatrix(
  symbols: string[],
  periodDays: number = 30
): Promise<CorrelationMatrixResponse> {
  const { data } = await api.get("/api/correlation", {
    params: { symbols: symbols.join(","), period_days: periodDays },
  })
  return data
}

// Stress Testing
export interface StressScenario {
  name: string
  price_change_percent: number
  iv_change_percent: number
  time_decay_days: number
}

export interface StressResult {
  scenario: StressScenario
  portfolio_pnl: number
  portfolio_pnl_percent: number
  position_impacts: Array<{
    position_id: string
    symbol: string
    pnl: number
    pnl_percent: number
  }>
}

export interface StressTestResponse {
  portfolio_value: number
  results: StressResult[]
  timestamp: string
}

export async function runStressTest(
  scenarios?: StressScenario[]
): Promise<StressTestResponse> {
  const { data } = await api.post("/api/stress-test", { scenarios })
  return data
}

// =============================================================================
// JPM VOLATILITY RESEARCH TYPES & API
// =============================================================================

export type JPMStrategyType = "call_overwriting" | "call_buying" | "put_underwriting" | "put_buying"
export type JPMScreenType = "rich_iv" | "cheap_iv" | "iv_top_movers" | "iv_bottom_movers" | "range_bound" | "trending"

export interface JPMTradingCandidate {
  ticker: string
  strategy: JPMStrategyType
  iv30: number
  iv_percentile: number
  hv30: number | null
  iv_hv_spread: number | null
  skew: number | null
  rationale: string
}

export interface JPMVolatilityScreen {
  ticker: string
  screen_type: JPMScreenType
  iv30: number
  iv60: number | null
  iv90: number | null
  iv_percentile: number
  iv_change_1w: number | null
  iv_change_1m: number | null
  hv30: number | null
  price: number | null
  price_change_1m: number | null
}

export interface JPMStockData {
  ticker: string
  price: number | null
  price_change_1d: number | null
  price_change_1m: number | null
  iv30: number
  iv60: number | null
  iv90: number | null
  iv_percentile: number
  iv_rank: number | null
  hv30: number | null
  hv60: number | null
  iv_hv_spread: number | null
  skew: number | null
  put_skew: number | null
  call_skew: number | null
  term_structure: "contango" | "backwardation" | "flat" | null
  sector: string | null
}

export interface JPMReportMetadata {
  report_date: string
  report_title: string
  source: string
  total_stocks: number
  last_updated: string
}

export interface JPMTradingCandidatesResponse {
  candidates: JPMTradingCandidate[]
}

export interface JPMVolatilityScreenResponse {
  screens: JPMVolatilityScreen[]
}

export interface JPMStocksResponse {
  stocks: JPMStockData[]
  total: number
}

// JPM API functions

export async function getJPMReport(): Promise<JPMReportMetadata> {
  const { data } = await api.get("/api/jpm/report")
  return data
}

export async function getJPMTradingCandidates(
  strategy?: JPMStrategyType
): Promise<JPMTradingCandidatesResponse> {
  const { data } = await api.get("/api/jpm/trading-candidates", {
    params: strategy ? { strategy } : {},
  })
  return data
}

export async function getJPMVolatilityScreen(
  screenType?: JPMScreenType
): Promise<JPMVolatilityScreenResponse> {
  const { data } = await api.get("/api/jpm/volatility-screen", {
    params: screenType ? { screen_type: screenType } : {},
  })
  return data
}

export interface JPMStocksParams {
  sort_by?: string
  ascending?: boolean
  sector?: string
  iv_percentile_min?: number
  iv_percentile_max?: number
}

export async function getJPMStocks(params?: JPMStocksParams): Promise<JPMStocksResponse> {
  const { data } = await api.get("/api/jpm/stocks", { params })
  return data
}

export async function getJPMStock(ticker: string): Promise<JPMStockData> {
  const { data } = await api.get(`/api/jpm/stock/${ticker}`)
  return data
}

// =============================================================================
// FEAR/GREED INDEX TYPES & API
// =============================================================================

export interface FearGreedComponent {
  name: string
  description: string
  score: number
}

export interface FearGreedResponse {
  score: number
  classification: string
  previous_close: number
  week_ago: number
  components: Record<string, FearGreedComponent>
  timestamp: string
}

export async function getFearGreedIndex(): Promise<FearGreedResponse> {
  const { data } = await api.get("/api/fear-greed")
  return data
}

// =============================================================================
// MARKET INDICATORS TYPES & API
// =============================================================================

export interface BondRatesData {
  tnx_yield: number
  irx_yield: number
  yield_spread: number
  tlt_price: number
  tlt_change: number | null
  tlt_change_percent: number | null
  timestamp: string
}

export interface CommoditiesData {
  gold_price: number
  gold_change: number | null
  gold_change_percent: number | null
  oil_price: number
  oil_change: number | null
  oil_change_percent: number | null
  dollar_price: number
  dollar_change: number | null
  dollar_change_percent: number | null
  timestamp: string
}

export interface SectorData {
  symbol: string
  name: string
  price: number
  change: number | null
  change_percent: number | null
}

export interface MarketBreadthData {
  advances: number
  declines: number
  advance_decline_ratio: number
  new_highs: number
  new_lows: number
  highs_lows_ratio: number
  mcclellan_oscillator: number | null
  timestamp: string
}

export interface MarketIndicatorsResponse {
  bonds: BondRatesData
  commodities: CommoditiesData
  sectors: SectorData[]
  breadth: MarketBreadthData
  timestamp: string
}

export async function getMarketIndicators(): Promise<MarketIndicatorsResponse> {
  const { data } = await api.get("/api/market-indicators")
  return data
}

// =============================================================================
// MCP SERVER TYPES & API
// =============================================================================

export interface MCPServerStatus {
  id: string
  name: string
  enabled: boolean
  status: "connected" | "disconnected" | "error" | "connecting"
  tools: string[]
  tool_count: number
  error: string | null
  connected_at: string | null
  call_count: number
  avg_response_ms: number
  capabilities: string[]
}

export interface MCPServersResponse {
  servers: MCPServerStatus[]
}

export interface MCPToolsResponse {
  server_id: string
  tools: string[]
  count: number
}

export async function getMCPServers(): Promise<MCPServersResponse> {
  const { data } = await api.get("/api/mcp-servers")
  return data
}

export async function getMCPServer(serverId: string): Promise<MCPServerStatus> {
  const { data } = await api.get(`/api/mcp-servers/${serverId}`)
  return data
}

export async function getMCPServerTools(serverId: string): Promise<MCPToolsResponse> {
  const { data } = await api.get(`/api/mcp-servers/${serverId}/tools`)
  return data
}

export async function toggleMCPServer(serverId: string): Promise<MCPServerStatus> {
  const { data } = await api.post(`/api/mcp-servers/${serverId}/toggle`)
  return data
}

export async function reconnectMCPServer(serverId: string): Promise<MCPServerStatus> {
  const { data } = await api.post(`/api/mcp-servers/${serverId}/reconnect`)
  return data
}

// =============================================================================
// TYPE ALIAS FOR COMPATIBILITY
// =============================================================================

type float = number
