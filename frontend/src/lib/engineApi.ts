import { api } from "./api"

// ── Engine Types ─────────────────────────────────────────────────────────

export type VolRegime =
  | "VERY_LOW" | "LOW" | "NORMAL" | "ELEVATED"
  | "HIGH" | "EXTREME" | "CRISIS" | "LIQUIDITY_STRESS"

export type Trend =
  | "STRONG_UPTREND" | "UPTREND" | "RANGE_BOUND"
  | "DOWNTREND" | "STRONG_DOWNTREND"

export type Confidence = "HIGH" | "MEDIUM" | "LOW"
export type EventType = "FOMC" | "CPI" | "NFP" | "EARNINGS" | "NONE"
export type RulePriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
export type RecommendationType =
  | "TRADE" | "TRADE_CAUTIOUS" | "LOW_CONVICTION"
  | "NO_TRADE" | "REGIME_UNCERTAIN"

export interface RegimeResult {
  regime: VolRegime
  trend: Trend
  event_active: boolean
  event_type: EventType
  multi_event: boolean
  vol_unstable: boolean
  confidence: Confidence
  confirming_signals: number
  actions: string[]
  timestamp: string
}

export interface StrategyScore {
  total: number
  edge: number
  carry_fit: number
  tail_risk: number
  robustness: number
  liquidity: number
  complexity: number
}

export interface StrategyParams {
  delta: number | null
  deltas: Record<string, number> | null
  dte: number
  size_multiplier: number
  profit_target: number | string
  stop_loss: number | string
  roll_dte: number | null
}

export interface GateCheckResult {
  gate_name: string
  passed: boolean
  reason: string
}

export interface StrategyTemplate {
  name: string
  family: string
  objective: string
  legs: number
  base_delta: number | Record<string, number>
  base_dte: number | string
  description: string
  regime_allowed: string[]
  regime_excluded: string[]
  win_rate: number | null
  sharpe_hist: number | null
  structure: string | null
}

export interface StrategyCandidate {
  name: string
  template: StrategyTemplate
  scores: StrategyScore
  params: StrategyParams
  gates: GateCheckResult[]
}

export interface StrategyRecommendation {
  recommendation: RecommendationType
  strategies: StrategyCandidate[]
  regime: RegimeResult
  note: string
  timestamp: string
}

export interface RuleEvaluation {
  rule_id: string
  rule_name: string
  triggered: boolean
  priority: RulePriority
  action: string
  details: string
}

export interface PositionHealthCheck {
  position_id: string
  adjustment_rules: RuleEvaluation[]
  exit_rules: RuleEvaluation[]
  triggered_count: number
  critical_count: number
  recommended_action: string
}

export interface EarlyWarningSignal {
  signal: string
  action: string
  lead_time: string
  triggered: boolean
  current_value: number | null
  threshold: number | null
}

export interface HedgeInstrument {
  name: string
  allocation: number
  structure: string
  tenor: string
  rationale: string
}

export interface TailTradingStatus {
  signal_active: boolean
  ts_value: number
  delta_pillar_active: boolean
  gamma_pillar_active: boolean
  vega_pillar_active: boolean
}

export interface TailRiskAssessment {
  hedge_allocation: {
    annual_budget_pct: number
    instruments: HedgeInstrument[]
  }
  early_warnings: EarlyWarningSignal[]
  active_warnings_count: number
  crisis_protocol_active: boolean
  crisis_actions: string[]
  tail_trading: TailTradingStatus
  timestamp: string
}

export interface ConflictScenario {
  conflict_id: string
  description: string
  signal_a: string
  signal_b: string
  resolution: string
  detected: boolean
}

export interface PlaybookPhaseDetail {
  phase: string
  timing: string
  iv_behavior: string
  strategy: string
  sizing: string
  notes: string[]
}

export interface EventPlaybook {
  event_type: EventType
  phases: PlaybookPhaseDetail[]
  notes: string[]
  key_rules: string[]
}

export interface ZeroDTEDayInfo {
  day: string
  premium: string
  bias: string
  gamma_imbalance: string
}

export interface ZeroDTEPlaybook {
  characteristics: Record<string, unknown>
  days: ZeroDTEDayInfo[]
  entry_rule: string
  event_block: string
}

export interface FullAnalysisResult {
  regime: RegimeResult
  recommendation: StrategyRecommendation
  tail_risk: TailRiskAssessment
  conflicts: ConflictScenario[]
  active_playbook: EventPlaybook | null
  position_health: PositionHealthCheck[]
  timestamp: string
}

// ── API Functions ────────────────────────────────────────────────────────

export async function getEngineRegime(): Promise<RegimeResult> {
  const { data } = await api.get("/api/engine/regime")
  return data
}

export async function getEngineRegimeHistory(): Promise<{
  current: RegimeResult
  previous: RegimeResult | null
}> {
  const { data } = await api.get("/api/engine/regime/history")
  return data
}

export async function getEngineRecommendations(
  nav: number = 100_000,
  objective: string = "income"
): Promise<StrategyRecommendation> {
  const { data } = await api.post("/api/engine/recommend", { nav, objective })
  return data
}

export async function getEngineAnalysis(
  nav: number = 100_000,
  objective: string = "income",
  positions?: Record<string, unknown>[]
): Promise<FullAnalysisResult> {
  const { data } = await api.post("/api/engine/analysis", { nav, objective, positions })
  return data
}

export async function getEngineStrategies(): Promise<StrategyTemplate[]> {
  const { data } = await api.get("/api/engine/strategies")
  return data
}

export async function getEngineStrategiesByFamily(
  family: string
): Promise<StrategyTemplate[]> {
  const { data } = await api.get(`/api/engine/strategies/${family}`)
  return data
}

export async function getEngineTailRisk(): Promise<TailRiskAssessment> {
  const { data } = await api.get("/api/engine/tail-risk")
  return data
}

export async function getEngineEarlyWarnings(): Promise<{
  warnings: EarlyWarningSignal[]
  active_count: number
  crisis_active: boolean
}> {
  const { data } = await api.get("/api/engine/early-warnings")
  return data
}

export async function getEngineConflicts(): Promise<ConflictScenario[]> {
  const { data } = await api.get("/api/engine/conflicts")
  return data
}

export async function getEngineActiveConflicts(): Promise<ConflictScenario[]> {
  const { data } = await api.get("/api/engine/conflicts/active")
  return data
}

export async function evaluateEnginePosition(
  position: Record<string, unknown>
): Promise<PositionHealthCheck> {
  const { data } = await api.post("/api/engine/positions/evaluate", { position })
  return data
}

export async function getEnginePlaybook(
  eventType: string
): Promise<EventPlaybook> {
  const { data } = await api.get(`/api/engine/playbook/${eventType}`)
  return data
}

export async function getEngineZeroDTE(): Promise<ZeroDTEPlaybook> {
  const { data } = await api.get("/api/engine/playbook/0dte/info")
  return data
}

export async function getEngineZeroDTEDay(
  day: string
): Promise<ZeroDTEDayInfo> {
  const { data } = await api.get(`/api/engine/playbook/0dte/${day}`)
  return data
}

export async function getEngineReferenceTables(): Promise<{ tables: string[] }> {
  const { data } = await api.get("/api/engine/reference")
  return data
}

export async function getEngineReferenceTable(
  tableName: string
): Promise<Record<string, unknown>[]> {
  const { data } = await api.get(`/api/engine/reference/${tableName}`)
  return data
}
