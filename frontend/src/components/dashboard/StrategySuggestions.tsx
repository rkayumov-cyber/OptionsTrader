import { useStrategySuggestions } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Lightbulb, TrendingUp, TrendingDown, Minus, AlertCircle } from "lucide-react"
import type { Market } from "@/lib/api"

interface StrategySuggestionsProps {
  symbol: string
  market: Market
  className?: string
}

const getRiskColorVar = (risk: string) => {
  switch (risk) {
    case "low":
      return "var(--bb-green)"
    case "medium":
      return "var(--bb-amber)"
    case "high":
      return "var(--bb-red)"
    default:
      return "var(--bb-muted)"
  }
}

const getConditionIcon = (value: string) => {
  if (value.includes("bullish") || value === "increasing" || value === "high")
    return <TrendingUp className="h-3 w-3" />
  if (value.includes("bearish") || value === "decreasing" || value === "low")
    return <TrendingDown className="h-3 w-3" />
  return <Minus className="h-3 w-3" />
}

const getConditionColorVar = (key: string, value: string) => {
  if (key === "vix_level") {
    if (value === "low") return "var(--bb-green)"
    if (value === "normal") return "var(--bb-green)"
    if (value === "elevated") return "var(--bb-orange)"
    if (value === "high") return "var(--bb-red)"
  }
  if (key === "iv_rank") {
    if (value === "low") return "var(--bb-blue)"
    if (value === "medium") return "var(--bb-cyan)"
    if (value === "high") return "var(--bb-red)"
  }
  if (key === "trend") {
    if (value.includes("bullish")) return "var(--bb-green)"
    if (value.includes("bearish")) return "var(--bb-red)"
    return "var(--bb-amber)"
  }
  return "var(--bb-muted)"
}

export function StrategySuggestions({ symbol, market, className }: StrategySuggestionsProps) {
  const { data, isLoading } = useStrategySuggestions(symbol, market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-bb-amber" />
            Strategy Suggestions
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-bb-amber" />
            Strategy Suggestions
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <Lightbulb className="h-8 w-8 mb-2 opacity-50" />
          <p className="text-sm">No suggestions available</p>
        </CardContent>
      </Card>
    )
  }

  const conditions = data.market_conditions
  const suggestions = data.suggestions

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-bb-amber" />
            Strategy Suggestions
          </div>
          <span className="text-sm font-normal text-muted-foreground">{symbol}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Market Conditions */}
        <div className="flex flex-wrap gap-2">
          {Object.entries(conditions).map(([key, value]) => (
            <div
              key={key}
              className="flex items-center gap-1 px-2 py-1 rounded-full text-xs"
              style={{
                backgroundColor: `hsl(${getConditionColorVar(key, value)} / 0.1)`,
                color: `hsl(${getConditionColorVar(key, value)})`,
              }}
            >
              {getConditionIcon(value)}
              <span className="capitalize">
                {key.replace("_", " ")}: {value.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>

        {/* Strategy Cards */}
        <div className="grid gap-3">
          {suggestions.map((strategy, index) => (
            <div
              key={strategy.strategy}
              className="p-3 rounded-lg bg-muted/50 border border-transparent hover:border-primary/20 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h4 className="font-medium text-sm">{strategy.display_name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span
                      className="text-[10px] px-1.5 py-0.5 rounded-full"
                      style={{
                        backgroundColor: `hsl(${getRiskColorVar(strategy.risk_level)} / 0.1)`,
                        color: `hsl(${getRiskColorVar(strategy.risk_level)})`,
                      }}
                    >
                      {strategy.risk_level} risk
                    </span>
                    {index === 0 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary">
                        Top Pick
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold tabular-nums text-primary">
                    {strategy.suitability.toFixed(0)}
                  </div>
                  <div className="text-xs text-muted-foreground">score</div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground mb-2">{strategy.reasoning}</p>
              <div className="flex gap-4 text-xs">
                {strategy.max_profit && (
                  <div>
                    <span className="text-muted-foreground">Max Profit: </span>
                    <span className="text-bb-green">{strategy.max_profit}</span>
                  </div>
                )}
                {strategy.max_loss && (
                  <div>
                    <span className="text-muted-foreground">Max Loss: </span>
                    <span className="text-bb-red">{strategy.max_loss}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <AlertCircle className="h-3.5 w-3.5" />
          <span>Suggestions are for educational purposes. Always do your own research.</span>
        </div>
      </CardContent>
    </Card>
  )
}
