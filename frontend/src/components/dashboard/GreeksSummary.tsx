import { useOptionChain } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, TrendingDown, Clock, Activity } from "lucide-react"
import type { Market } from "@/lib/api"

interface GreeksSummaryProps {
  symbol: string
  market: Market
  className?: string
}

interface GreekCardProps {
  title: string
  value: number
  unit: string
  icon: React.ReactNode
  description: string
  colorVar: string
}

function GreekCard({ title, value, unit, icon, description, colorVar }: GreekCardProps) {
  const isPositive = value >= 0

  return (
    <div className="bg-muted/50 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <div style={{ color: `hsl(${colorVar})` }} className="opacity-80">
          {icon}
        </div>
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{title}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span
          className="text-xl font-bold tabular-nums"
          style={{ color: `hsl(${colorVar})` }}
        >
          {isPositive ? "+" : ""}
          {value.toFixed(2)}
        </span>
        <span className="text-xs text-muted-foreground">{unit}</span>
      </div>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  )
}

export function GreeksSummary({ symbol, market, className }: GreeksSummaryProps) {
  const { data: chain, isLoading } = useOptionChain(symbol, market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Greeks Summary</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (!chain || (chain.calls.length === 0 && chain.puts.length === 0)) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Greeks Summary</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
          No options data available
        </CardContent>
      </Card>
    )
  }

  // Aggregate Greeks from all options (simulate portfolio)
  // In reality, this would be based on actual positions
  const aggregateGreeks = {
    delta: 0,
    gamma: 0,
    theta: 0,
    vega: 0,
  }

  // Sum up Greeks from ATM options (as an example)
  const allOptions = [...chain.calls, ...chain.puts]
  const optionsWithGreeks = allOptions.filter((opt) => opt.greeks)

  if (optionsWithGreeks.length > 0) {
    // Take first few options as sample portfolio
    const sampleOptions = optionsWithGreeks.slice(0, 10)
    sampleOptions.forEach((opt) => {
      if (opt.greeks) {
        aggregateGreeks.delta += opt.greeks.delta
        aggregateGreeks.gamma += opt.greeks.gamma
        aggregateGreeks.theta += opt.greeks.theta
        aggregateGreeks.vega += opt.greeks.vega
      }
    })
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Greeks Summary</span>
          <span className="text-sm font-normal text-muted-foreground">{symbol}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <GreekCard
            title="Delta"
            value={aggregateGreeks.delta * 100}
            unit="shares"
            icon={<TrendingUp className="h-3.5 w-3.5" />}
            description="Directional exposure"
            colorVar={aggregateGreeks.delta >= 0 ? "var(--bb-green)" : "var(--bb-red)"}
          />
          <GreekCard
            title="Gamma"
            value={aggregateGreeks.gamma * 100}
            unit="per $1"
            icon={<Activity className="h-3.5 w-3.5" />}
            description="Delta sensitivity"
            colorVar="var(--bb-blue)"
          />
          <GreekCard
            title="Theta"
            value={aggregateGreeks.theta}
            unit="$/day"
            icon={<Clock className="h-3.5 w-3.5" />}
            description="Time decay"
            colorVar={aggregateGreeks.theta >= 0 ? "var(--bb-green)" : "var(--bb-red)"}
          />
          <GreekCard
            title="Vega"
            value={aggregateGreeks.vega}
            unit="per 1%"
            icon={<TrendingDown className="h-3.5 w-3.5" />}
            description="IV sensitivity"
            colorVar="var(--bb-cyan)"
          />
        </div>
        <p className="text-xs text-muted-foreground mt-3 text-center">
          Based on sample ATM options. Add positions for accurate portfolio Greeks.
        </p>
      </CardContent>
    </Card>
  )
}
