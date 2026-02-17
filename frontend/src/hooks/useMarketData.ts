import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  getQuote,
  getOptionChain,
  getVolatilitySurface,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
  getProviders,
  switchProvider,
  getPriceHistory,
  getIVAnalysis,
  getMarketSentiment,
  getUnusualActivity,
  getStrategySuggestions,
  // Payoff
  calculatePayoff,
  calculateTimeSeriesPayoff,
  getPayoffTemplate,
  getPayoffStrategies,
  // Positions
  getPositions,
  getPosition,
  createPosition,
  updatePosition,
  deletePosition,
  closePosition,
  getPortfolioSummary,
  // Scanner
  scanOptions,
  getHighIVOpportunities,
  getLowIVOpportunities,
  getHighVolumeActivity,
  // Paper Trading
  createPaperAccount,
  getPaperAccount,
  getDefaultPaperAccount,
  getAllPaperAccounts,
  placePaperOrder,
  getPaperOrders,
  getPaperPositions,
  cancelPaperOrder,
  resetPaperAccount,
  // Journal
  getJournalTrades,
  getJournalTrade,
  createJournalTrade,
  updateJournalTrade,
  closeJournalTrade,
  deleteJournalTrade,
  getJournalStats,
  getTradesBySymbol,
  getTradesByStrategy,
  // Alerts
  getAlertRules,
  getAlertRule,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  toggleAlertRule,
  getAlertNotifications,
  getUnacknowledgedAlerts,
  acknowledgeAlert,
  acknowledgeAllAlerts,
  deleteAlertNotification,
  checkAlerts,
  // Analytics
  calculateProbability,
  getIVHistory,
  getTermStructure,
  getSkewAnalysis,
  // Risk
  getEarningsCalendar,
  getCorrelationMatrix,
  runStressTest,
  // JPM Research
  getJPMReport,
  getJPMTradingCandidates,
  getJPMVolatilityScreen,
  getJPMStocks,
  getJPMStock,
  // Market Indicators
  getMarketIndicators,
  // Types
  type Market,
  type SwitchProviderRequest,
  type PayoffRequest,
  type TimeSeriesPayoffRequest,
  type CreatePositionRequest,
  type ScanCriteria,
  type CreatePaperAccountRequest,
  type PlaceOrderRequest,
  type CreateTradeRequest,
  type CloseTradeRequest,
  type CreateAlertRuleRequest,
  type StressScenario,
  type JPMStrategyType,
  type JPMScreenType,
  type JPMStocksParams,
} from "@/lib/api"

export function useQuote(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["quote", symbol, market],
    queryFn: () => getQuote(symbol, market),
    enabled: enabled && !!symbol,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 10000,
  })
}

// Real-time quote with faster updates for streaming display
export function useStreamingQuote(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["quote", symbol, market],
    queryFn: () => getQuote(symbol, market),
    enabled: enabled && !!symbol,
    refetchInterval: 5000, // Refresh every 5 seconds for real-time feel
    staleTime: 3000,
  })
}

export function useOptionChain(
  symbol: string,
  market: Market,
  expiration?: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ["optionChain", symbol, market, expiration],
    queryFn: () => getOptionChain(symbol, market, expiration),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

export function useVolatilitySurface(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["volatilitySurface", symbol, market],
    queryFn: () => getVolatilitySurface(symbol, market),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

export function useWatchlist() {
  return useQuery({
    queryKey: ["watchlist"],
    queryFn: getWatchlist,
    staleTime: 30000,
  })
}

export function usePriceHistory(
  symbol: string,
  market: Market,
  interval: string = "1d",
  limit: number = 30,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ["priceHistory", symbol, market, interval, limit],
    queryFn: () => getPriceHistory(symbol, market, interval, limit),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

export function useAddToWatchlist() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ symbol, market, name }: { symbol: string; market: Market; name?: string }) =>
      addToWatchlist(symbol, market, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] })
    },
  })
}

export function useRemoveFromWatchlist() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ symbol, market }: { symbol: string; market: Market }) =>
      removeFromWatchlist(symbol, market),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["watchlist"] })
    },
  })
}

export function useProviders() {
  return useQuery({
    queryKey: ["providers"],
    queryFn: getProviders,
    staleTime: 60000,
  })
}

export function useSwitchProvider() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: SwitchProviderRequest) => switchProvider(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["providers"] })
      queryClient.invalidateQueries({ queryKey: ["quote"] })
      queryClient.invalidateQueries({ queryKey: ["optionChain"] })
      queryClient.invalidateQueries({ queryKey: ["volatilitySurface"] })
    },
  })
}

// Dashboard hooks

export function useIVAnalysis(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["ivAnalysis", symbol, market],
    queryFn: () => getIVAnalysis(symbol, market),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

export function useMarketSentiment(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["marketSentiment", symbol, market],
    queryFn: () => getMarketSentiment(symbol, market),
    enabled: enabled && !!symbol,
    staleTime: 30000,
    refetchInterval: 30000,
  })
}

export function useUnusualActivity(market?: Market) {
  return useQuery({
    queryKey: ["unusualActivity", market],
    queryFn: () => getUnusualActivity(market),
    staleTime: 30000,
    refetchInterval: 60000,
  })
}

export function useStrategySuggestions(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["strategySuggestions", symbol, market],
    queryFn: () => getStrategySuggestions(symbol, market),
    enabled: enabled && !!symbol,
    staleTime: 120000,
  })
}

// =============================================================================
// PAYOFF DIAGRAM HOOKS
// =============================================================================

export function useCalculatePayoff() {
  return useMutation({
    mutationFn: (request: PayoffRequest) => calculatePayoff(request),
  })
}

export function useCalculateTimeSeriesPayoff() {
  return useMutation({
    mutationFn: (request: TimeSeriesPayoffRequest) => calculateTimeSeriesPayoff(request),
  })
}

export function usePayoffTemplate(strategy: string, underlyingPrice: number, enabled: boolean = true) {
  return useQuery({
    queryKey: ["payoffTemplate", strategy, underlyingPrice],
    queryFn: () => getPayoffTemplate(strategy, underlyingPrice),
    enabled: enabled && !!strategy && underlyingPrice > 0,
    staleTime: Infinity,
  })
}

export function usePayoffStrategies() {
  return useQuery({
    queryKey: ["payoffStrategies"],
    queryFn: getPayoffStrategies,
    staleTime: Infinity,
  })
}

// =============================================================================
// POSITION TRACKER HOOKS
// =============================================================================

export function usePositions() {
  return useQuery({
    queryKey: ["positions"],
    queryFn: getPositions,
    staleTime: 30000,
  })
}

export function usePosition(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["position", id],
    queryFn: () => getPosition(id),
    enabled: enabled && !!id,
    staleTime: 30000,
  })
}

export function useCreatePosition() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: CreatePositionRequest) => createPosition(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["positions"] })
      queryClient.invalidateQueries({ queryKey: ["portfolioSummary"] })
    },
  })
}

export function useUpdatePosition() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CreatePositionRequest> }) =>
      updatePosition(id, updates),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["positions"] })
      queryClient.invalidateQueries({ queryKey: ["position", id] })
      queryClient.invalidateQueries({ queryKey: ["portfolioSummary"] })
    },
  })
}

export function useDeletePosition() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deletePosition(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["positions"] })
      queryClient.invalidateQueries({ queryKey: ["portfolioSummary"] })
    },
  })
}

export function useClosePosition() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, exitPremiums }: { id: string; exitPremiums: Record<string, number> }) =>
      closePosition(id, exitPremiums),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["positions"] })
      queryClient.invalidateQueries({ queryKey: ["position", id] })
      queryClient.invalidateQueries({ queryKey: ["portfolioSummary"] })
    },
  })
}

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ["portfolioSummary"],
    queryFn: getPortfolioSummary,
    staleTime: 30000,
    refetchInterval: 60000,
  })
}

// =============================================================================
// OPTIONS SCANNER HOOKS
// =============================================================================

export function useScanOptions() {
  return useMutation({
    mutationFn: (criteria: ScanCriteria) => scanOptions(criteria),
  })
}

export function useHighIVOpportunities(market: Market = "US", enabled: boolean = true) {
  return useQuery({
    queryKey: ["scanner", "highIV", market],
    queryFn: () => getHighIVOpportunities(market),
    enabled,
    staleTime: 60000,
  })
}

export function useLowIVOpportunities(market: Market = "US", enabled: boolean = true) {
  return useQuery({
    queryKey: ["scanner", "lowIV", market],
    queryFn: () => getLowIVOpportunities(market),
    enabled,
    staleTime: 60000,
  })
}

export function useHighVolumeActivity(market: Market = "US", enabled: boolean = true) {
  return useQuery({
    queryKey: ["scanner", "highVolume", market],
    queryFn: () => getHighVolumeActivity(market),
    enabled,
    staleTime: 60000,
  })
}

// =============================================================================
// PAPER TRADING HOOKS
// =============================================================================

export function useCreatePaperAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request?: CreatePaperAccountRequest) => createPaperAccount(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["paperAccounts"] })
    },
  })
}

export function usePaperAccount(accountId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["paperAccount", accountId],
    queryFn: () => getPaperAccount(accountId),
    enabled: enabled && !!accountId,
    staleTime: 10000,
    refetchInterval: 30000,
  })
}

export function useDefaultPaperAccount() {
  return useQuery({
    queryKey: ["paperAccount", "default"],
    queryFn: getDefaultPaperAccount,
    staleTime: 10000,
    refetchInterval: 30000,
  })
}

export function useAllPaperAccounts() {
  return useQuery({
    queryKey: ["paperAccounts"],
    queryFn: getAllPaperAccounts,
    staleTime: 30000,
  })
}

export function usePlacePaperOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: PlaceOrderRequest) => placePaperOrder(request),
    onSuccess: (_, { account_id }) => {
      // Invalidate both specific account and default account queries
      queryClient.invalidateQueries({ queryKey: ["paperAccount", account_id] })
      queryClient.invalidateQueries({ queryKey: ["paperAccount", "default"] })
      queryClient.invalidateQueries({ queryKey: ["paperOrders", account_id] })
      queryClient.invalidateQueries({ queryKey: ["paperPositions", account_id] })
    },
  })
}

export function usePaperOrders(accountId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["paperOrders", accountId],
    queryFn: () => getPaperOrders(accountId),
    enabled: enabled && !!accountId,
    staleTime: 10000,
  })
}

export function usePaperPositions(accountId: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["paperPositions", accountId],
    queryFn: () => getPaperPositions(accountId),
    enabled: enabled && !!accountId,
    staleTime: 10000,
  })
}

export function useCancelPaperOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ accountId, orderId }: { accountId: string; orderId: string }) =>
      cancelPaperOrder(accountId, orderId),
    onSuccess: (_, { accountId }) => {
      queryClient.invalidateQueries({ queryKey: ["paperAccount", accountId] })
      queryClient.invalidateQueries({ queryKey: ["paperOrders", accountId] })
    },
  })
}

export function useResetPaperAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (accountId: string) => resetPaperAccount(accountId),
    onSuccess: (_, accountId) => {
      // Invalidate both specific account and default account queries
      queryClient.invalidateQueries({ queryKey: ["paperAccount", accountId] })
      queryClient.invalidateQueries({ queryKey: ["paperAccount", "default"] })
      queryClient.invalidateQueries({ queryKey: ["paperOrders", accountId] })
      queryClient.invalidateQueries({ queryKey: ["paperPositions", accountId] })
    },
  })
}

// =============================================================================
// TRADE JOURNAL HOOKS
// =============================================================================

export function useJournalTrades() {
  return useQuery({
    queryKey: ["journalTrades"],
    queryFn: getJournalTrades,
    staleTime: 30000,
  })
}

export function useJournalTrade(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["journalTrade", id],
    queryFn: () => getJournalTrade(id),
    enabled: enabled && !!id,
    staleTime: 30000,
  })
}

export function useCreateJournalTrade() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: CreateTradeRequest) => createJournalTrade(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journalTrades"] })
      queryClient.invalidateQueries({ queryKey: ["journalStats"] })
    },
  })
}

export function useUpdateJournalTrade() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CreateTradeRequest> }) =>
      updateJournalTrade(id, updates),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["journalTrades"] })
      queryClient.invalidateQueries({ queryKey: ["journalTrade", id] })
      queryClient.invalidateQueries({ queryKey: ["journalStats"] })
    },
  })
}

export function useCloseJournalTrade() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: CloseTradeRequest }) =>
      closeJournalTrade(id, request),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["journalTrades"] })
      queryClient.invalidateQueries({ queryKey: ["journalTrade", id] })
      queryClient.invalidateQueries({ queryKey: ["journalStats"] })
    },
  })
}

export function useDeleteJournalTrade() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteJournalTrade(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["journalTrades"] })
      queryClient.invalidateQueries({ queryKey: ["journalStats"] })
    },
  })
}

export function useJournalStats() {
  return useQuery({
    queryKey: ["journalStats"],
    queryFn: getJournalStats,
    staleTime: 60000,
  })
}

export function useTradesBySymbol(symbol: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["journalTrades", "symbol", symbol],
    queryFn: () => getTradesBySymbol(symbol),
    enabled: enabled && !!symbol,
    staleTime: 30000,
  })
}

export function useTradesByStrategy(strategy: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["journalTrades", "strategy", strategy],
    queryFn: () => getTradesByStrategy(strategy),
    enabled: enabled && !!strategy,
    staleTime: 30000,
  })
}

// =============================================================================
// ALERTS HOOKS
// =============================================================================

export function useAlertRules() {
  return useQuery({
    queryKey: ["alertRules"],
    queryFn: getAlertRules,
    staleTime: 30000,
  })
}

export function useAlertRule(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["alertRule", id],
    queryFn: () => getAlertRule(id),
    enabled: enabled && !!id,
    staleTime: 30000,
  })
}

export function useCreateAlertRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: CreateAlertRuleRequest) => createAlertRule(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] })
    },
  })
}

export function useUpdateAlertRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<CreateAlertRuleRequest> }) =>
      updateAlertRule(id, updates),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] })
      queryClient.invalidateQueries({ queryKey: ["alertRule", id] })
    },
  })
}

export function useDeleteAlertRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAlertRule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] })
    },
  })
}

export function useToggleAlertRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => toggleAlertRule(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["alertRules"] })
      queryClient.invalidateQueries({ queryKey: ["alertRule", id] })
    },
  })
}

export function useAlertNotifications() {
  return useQuery({
    queryKey: ["alertNotifications"],
    queryFn: getAlertNotifications,
    staleTime: 10000,
    refetchInterval: 30000,
  })
}

export function useUnacknowledgedAlerts() {
  return useQuery({
    queryKey: ["alertNotifications", "unacknowledged"],
    queryFn: getUnacknowledgedAlerts,
    staleTime: 10000,
    refetchInterval: 30000,
  })
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => acknowledgeAlert(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertNotifications"] })
    },
  })
}

export function useAcknowledgeAllAlerts() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => acknowledgeAllAlerts(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertNotifications"] })
    },
  })
}

export function useDeleteAlertNotification() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteAlertNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertNotifications"] })
    },
  })
}

export function useCheckAlerts() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (marketData: Record<string, Record<string, number>>) => checkAlerts(marketData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alertNotifications"] })
    },
  })
}

// =============================================================================
// ANALYTICS HOOKS
// =============================================================================

export function useCalculateProbability(
  symbol: string,
  market: Market,
  strike: number,
  dte: number,
  iv: number,
  strikeLower?: number,
  strikeUpper?: number,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: ["probability", symbol, market, strike, dte, iv, strikeLower, strikeUpper],
    queryFn: () => calculateProbability(symbol, market, strike, dte, iv, strikeLower, strikeUpper),
    enabled: enabled && !!symbol && strike > 0 && dte > 0 && iv > 0,
    staleTime: 60000,
  })
}

export function useIVHistory(symbol: string, market: Market, days: number = 90, enabled: boolean = true) {
  return useQuery({
    queryKey: ["ivHistory", symbol, market, days],
    queryFn: () => getIVHistory(symbol, market, days),
    enabled: enabled && !!symbol,
    staleTime: 300000, // 5 minutes
  })
}

export function useTermStructure(symbol: string, market: Market, enabled: boolean = true) {
  return useQuery({
    queryKey: ["termStructure", symbol, market],
    queryFn: () => getTermStructure(symbol, market),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

export function useSkewAnalysis(symbol: string, market: Market, expiration?: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["skew", symbol, market, expiration],
    queryFn: () => getSkewAnalysis(symbol, market, expiration),
    enabled: enabled && !!symbol,
    staleTime: 60000,
  })
}

// =============================================================================
// RISK MANAGEMENT HOOKS
// =============================================================================

export function useEarningsCalendar(symbols?: string[], days: number = 30, enabled: boolean = true) {
  return useQuery({
    queryKey: ["earnings", symbols, days],
    queryFn: () => getEarningsCalendar(symbols, days),
    enabled,
    staleTime: 300000, // 5 minutes
  })
}

export function useCorrelationMatrix(symbols: string[], periodDays: number = 30, enabled: boolean = true) {
  return useQuery({
    queryKey: ["correlation", symbols, periodDays],
    queryFn: () => getCorrelationMatrix(symbols, periodDays),
    enabled: enabled && symbols.length >= 2,
    staleTime: 300000, // 5 minutes
  })
}

export function useRunStressTest() {
  return useMutation({
    mutationFn: (scenarios?: StressScenario[]) => runStressTest(scenarios),
  })
}

// =============================================================================
// JPM VOLATILITY RESEARCH HOOKS
// =============================================================================

export function useJPMReport() {
  return useQuery({
    queryKey: ["jpm", "report"],
    queryFn: getJPMReport,
    staleTime: 300000, // 5 minutes
  })
}

export function useJPMTradingCandidates(strategy?: JPMStrategyType, enabled: boolean = true) {
  return useQuery({
    queryKey: ["jpm", "trading-candidates", strategy],
    queryFn: () => getJPMTradingCandidates(strategy),
    enabled,
    staleTime: 300000,
  })
}

export function useJPMVolatilityScreen(screenType?: JPMScreenType, enabled: boolean = true) {
  return useQuery({
    queryKey: ["jpm", "volatility-screen", screenType],
    queryFn: () => getJPMVolatilityScreen(screenType),
    enabled,
    staleTime: 300000,
  })
}

export function useJPMStocks(params?: JPMStocksParams, enabled: boolean = true) {
  return useQuery({
    queryKey: ["jpm", "stocks", params],
    queryFn: () => getJPMStocks(params),
    enabled,
    staleTime: 300000,
  })
}

export function useJPMStock(ticker: string, enabled: boolean = true) {
  return useQuery({
    queryKey: ["jpm", "stock", ticker],
    queryFn: () => getJPMStock(ticker),
    enabled: enabled && !!ticker,
    staleTime: 300000,
  })
}

// =============================================================================
// MARKET INDICATORS HOOKS
// =============================================================================

export function useMarketIndicators(enabled: boolean = true) {
  return useQuery({
    queryKey: ["marketIndicators"],
    queryFn: getMarketIndicators,
    enabled,
    refetchInterval: 30000, // Refresh every 30 seconds
    staleTime: 15000,
  })
}
