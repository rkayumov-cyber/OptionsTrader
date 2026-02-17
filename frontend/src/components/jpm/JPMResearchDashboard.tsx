import { useState } from "react"
import { FileText, TrendingUp, TrendingDown, BarChart3, Table2, RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
  useJPMReport,
  useJPMTradingCandidates,
  useJPMVolatilityScreen,
  useJPMStocks,
} from "@/hooks/useMarketData"
import type { JPMStrategyType, JPMScreenType, JPMTradingCandidate, JPMVolatilityScreen, JPMStockData, Market } from "@/lib/api"

interface JPMResearchDashboardProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
}

// Strategy display names and colors
const STRATEGY_CONFIG: Record<JPMStrategyType, { name: string; shortName: string; color: string; description: string }> = {
  call_overwriting: { name: "Call Overwriting", shortName: "CALL OW", color: "text-bb-cyan", description: "Sell covered calls for income" },
  call_buying: { name: "Call Buying", shortName: "CALL BUY", color: "text-bb-green", description: "Buy calls for upside exposure" },
  put_underwriting: { name: "Put Underwriting", shortName: "PUT UW", color: "text-bb-amber", description: "Sell cash-secured puts" },
  put_buying: { name: "Put Buying", shortName: "PUT BUY", color: "text-bb-red", description: "Buy puts for downside protection" },
}

const SCREEN_CONFIG: Record<JPMScreenType, { name: string; color: string }> = {
  rich_iv: { name: "Rich IV", color: "text-bb-red" },
  cheap_iv: { name: "Cheap IV", color: "text-bb-green" },
  iv_top_movers: { name: "IV Risers", color: "text-bb-amber" },
  iv_bottom_movers: { name: "IV Fallers", color: "text-bb-cyan" },
  range_bound: { name: "Range Bound", color: "text-muted-foreground" },
  trending: { name: "Trending", color: "text-primary" },
}

function TradingCandidateCard({
  strategy,
  candidates,
  onSymbolSelect,
}: {
  strategy: JPMStrategyType
  candidates: JPMTradingCandidate[]
  onSymbolSelect?: (symbol: string, market: Market) => void
}) {
  const config = STRATEGY_CONFIG[strategy]

  return (
    <Card className="h-full">
      <CardHeader className="py-2 px-3">
        <CardTitle className={`text-xs font-bold uppercase tracking-wider ${config.color}`}>
          {config.shortName}
        </CardTitle>
        <p className="text-[9px] text-muted-foreground">{config.description}</p>
      </CardHeader>
      <CardContent className="px-3 pb-2 pt-0">
        <div className="space-y-1">
          {candidates.slice(0, 5).map((candidate) => (
            <div
              key={candidate.ticker}
              className="flex items-center justify-between py-1 px-2 rounded hover:bg-muted/50 cursor-pointer border-l-2 border-transparent hover:border-primary transition-colors"
              onClick={() => onSymbolSelect?.(candidate.ticker, "US")}
            >
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sm text-bb-cyan">{candidate.ticker}</span>
              </div>
              <div className="flex items-center gap-3 text-[10px]">
                <div className="text-right">
                  <span className="text-muted-foreground">IV30:</span>
                  <span className="ml-1 font-mono price-value">{candidate.iv30.toFixed(1)}%</span>
                </div>
                <div className="text-right">
                  <span className="text-muted-foreground">%ile:</span>
                  <span className={`ml-1 font-mono ${candidate.iv_percentile > 70 ? "text-bb-red" : candidate.iv_percentile < 30 ? "text-bb-green" : "text-foreground"}`}>
                    {candidate.iv_percentile.toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function VolatilityScreenCard({
  screenType,
  screens,
  onSymbolSelect,
}: {
  screenType: JPMScreenType
  screens: JPMVolatilityScreen[]
  onSymbolSelect?: (symbol: string, market: Market) => void
}) {
  const config = SCREEN_CONFIG[screenType]

  return (
    <div className="space-y-1">
      <h4 className={`text-[10px] font-bold uppercase tracking-wider ${config.color}`}>
        {config.name}
      </h4>
      <div className="space-y-0.5">
        {screens.slice(0, 5).map((screen) => (
          <div
            key={screen.ticker}
            className="flex items-center justify-between py-0.5 px-1 rounded hover:bg-muted/50 cursor-pointer text-[10px]"
            onClick={() => onSymbolSelect?.(screen.ticker, "US")}
          >
            <span className="font-mono font-semibold text-bb-cyan">{screen.ticker}</span>
            <div className="flex items-center gap-2">
              <span className="font-mono price-value">{screen.iv30.toFixed(1)}%</span>
              {screen.iv_change_1w !== null && (
                <span className={`font-mono ${screen.iv_change_1w > 0 ? "text-bb-green" : "text-bb-red"}`}>
                  {screen.iv_change_1w > 0 ? "+" : ""}{screen.iv_change_1w.toFixed(1)}%
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StockDataTable({
  stocks,
  onSymbolSelect,
}: {
  stocks: JPMStockData[]
  onSymbolSelect?: (symbol: string, market: Market) => void
}) {
  const [sortBy, setSortBy] = useState<"ticker" | "iv30" | "iv_percentile" | "iv_hv_spread">("iv_percentile")
  const [sortAsc, setSortAsc] = useState(false)

  const handleSort = (column: typeof sortBy) => {
    if (sortBy === column) {
      setSortAsc(!sortAsc)
    } else {
      setSortBy(column)
      setSortAsc(false)
    }
  }

  const sortedStocks = [...stocks].sort((a, b) => {
    let aVal: number | string = 0
    let bVal: number | string = 0

    switch (sortBy) {
      case "ticker":
        aVal = a.ticker
        bVal = b.ticker
        break
      case "iv30":
        aVal = a.iv30
        bVal = b.iv30
        break
      case "iv_percentile":
        aVal = a.iv_percentile
        bVal = b.iv_percentile
        break
      case "iv_hv_spread":
        aVal = a.iv_hv_spread ?? 0
        bVal = b.iv_hv_spread ?? 0
        break
    }

    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal)
    }
    return sortAsc ? (aVal as number) - (bVal as number) : (bVal as number) - (aVal as number)
  })

  const SortHeader = ({ column, label }: { column: typeof sortBy; label: string }) => (
    <th
      className="px-2 py-1 text-left text-[9px] uppercase tracking-wider text-muted-foreground cursor-pointer hover:text-foreground"
      onClick={() => handleSort(column)}
    >
      {label}
      {sortBy === column && <span className="ml-1">{sortAsc ? "▲" : "▼"}</span>}
    </th>
  )

  return (
    <div className="overflow-auto max-h-64">
      <table className="w-full text-[10px]">
        <thead className="sticky top-0 bg-background">
          <tr className="border-b border-border">
            <SortHeader column="ticker" label="Ticker" />
            <SortHeader column="iv30" label="IV30" />
            <SortHeader column="iv_percentile" label="%ile" />
            <SortHeader column="iv_hv_spread" label="IV-HV" />
            <th className="px-2 py-1 text-left text-[9px] uppercase tracking-wider text-muted-foreground">Sector</th>
          </tr>
        </thead>
        <tbody>
          {sortedStocks.slice(0, 30).map((stock) => (
            <tr
              key={stock.ticker}
              className="border-b border-border/50 hover:bg-muted/50 cursor-pointer"
              onClick={() => onSymbolSelect?.(stock.ticker, "US")}
            >
              <td className="px-2 py-1 font-mono font-semibold text-bb-cyan">{stock.ticker}</td>
              <td className="px-2 py-1 font-mono price-value">{stock.iv30.toFixed(1)}%</td>
              <td className={`px-2 py-1 font-mono ${stock.iv_percentile > 70 ? "text-bb-red" : stock.iv_percentile < 30 ? "text-bb-green" : ""}`}>
                {stock.iv_percentile.toFixed(0)}
              </td>
              <td className={`px-2 py-1 font-mono ${(stock.iv_hv_spread ?? 0) > 0 ? "text-bb-amber" : "text-bb-cyan"}`}>
                {stock.iv_hv_spread !== null ? `${stock.iv_hv_spread > 0 ? "+" : ""}${stock.iv_hv_spread.toFixed(1)}` : "-"}
              </td>
              <td className="px-2 py-1 text-muted-foreground truncate max-w-[80px]">{stock.sector ?? "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function JPMResearchDashboard({ onSymbolSelect }: JPMResearchDashboardProps) {
  const { data: report } = useJPMReport()
  const { data: callOverwriting } = useJPMTradingCandidates("call_overwriting")
  const { data: callBuying } = useJPMTradingCandidates("call_buying")
  const { data: putUnderwriting } = useJPMTradingCandidates("put_underwriting")
  const { data: putBuying } = useJPMTradingCandidates("put_buying")
  const { data: richIV } = useJPMVolatilityScreen("rich_iv")
  const { data: cheapIV } = useJPMVolatilityScreen("cheap_iv")
  const { data: ivRisers } = useJPMVolatilityScreen("iv_top_movers")
  const { data: ivFallers } = useJPMVolatilityScreen("iv_bottom_movers")
  const { data: stocksData } = useJPMStocks({ sort_by: "iv_percentile", ascending: false })

  return (
    <div className="space-y-3">
      {/* Header */}
      <Card>
        <CardHeader className="py-2 px-4 flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="h-4 w-4 text-bb-amber" />
            <div>
              <CardTitle className="text-sm font-bold">
                {report?.report_title || "JPM Volatility Research"}
              </CardTitle>
              <p className="text-[10px] text-muted-foreground">
                {report?.source} | Report Date: {report?.report_date || "N/A"} | {report?.total_stocks || 0} stocks analyzed
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="live-indicator" />
            <span className="text-[10px] text-muted-foreground">
              Updated {report?.last_updated ? new Date(report.last_updated).toLocaleTimeString() : "N/A"}
            </span>
          </div>
        </CardHeader>
      </Card>

      {/* Trading Candidates Grid */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="h-3 w-3 text-bb-green" />
          <h3 className="text-xs font-bold uppercase tracking-wider">Trading Candidates</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
          <TradingCandidateCard
            strategy="call_overwriting"
            candidates={callOverwriting?.candidates || []}
            onSymbolSelect={onSymbolSelect}
          />
          <TradingCandidateCard
            strategy="call_buying"
            candidates={callBuying?.candidates || []}
            onSymbolSelect={onSymbolSelect}
          />
          <TradingCandidateCard
            strategy="put_underwriting"
            candidates={putUnderwriting?.candidates || []}
            onSymbolSelect={onSymbolSelect}
          />
          <TradingCandidateCard
            strategy="put_buying"
            candidates={putBuying?.candidates || []}
            onSymbolSelect={onSymbolSelect}
          />
        </div>
      </div>

      {/* Volatility Screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        <Card>
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-xs font-bold uppercase tracking-wider flex items-center gap-2">
              <BarChart3 className="h-3 w-3 text-bb-amber" />
              Volatility Screens
            </CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-2 pt-0">
            <div className="grid grid-cols-2 gap-4">
              <VolatilityScreenCard
                screenType="rich_iv"
                screens={richIV?.screens || []}
                onSymbolSelect={onSymbolSelect}
              />
              <VolatilityScreenCard
                screenType="cheap_iv"
                screens={cheapIV?.screens || []}
                onSymbolSelect={onSymbolSelect}
              />
              <VolatilityScreenCard
                screenType="iv_top_movers"
                screens={ivRisers?.screens || []}
                onSymbolSelect={onSymbolSelect}
              />
              <VolatilityScreenCard
                screenType="iv_bottom_movers"
                screens={ivFallers?.screens || []}
                onSymbolSelect={onSymbolSelect}
              />
            </div>
          </CardContent>
        </Card>

        {/* Stock Data Table */}
        <Card>
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-xs font-bold uppercase tracking-wider flex items-center gap-2">
              <Table2 className="h-3 w-3 text-bb-cyan" />
              All Stocks ({stocksData?.total || 0})
            </CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-2 pt-0">
            <StockDataTable
              stocks={stocksData?.stocks || []}
              onSymbolSelect={onSymbolSelect}
            />
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
      <div className="text-center text-[9px] text-muted-foreground py-1 border-t border-border">
        <span className="text-bb-green">Green</span>: Low IV (&lt;30%ile) |
        <span className="text-bb-red ml-1">Red</span>: High IV (&gt;70%ile) |
        <span className="text-bb-amber ml-1">Amber</span>: IV &gt; HV |
        <span className="text-bb-cyan ml-1">Cyan</span>: IV &lt; HV |
        <span className="ml-2">Click ticker to analyze</span>
      </div>
    </div>
  )
}
