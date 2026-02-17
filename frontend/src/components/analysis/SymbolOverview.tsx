import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PriceChart } from "@/components/PriceChart"
import { IVChart } from "@/components/analytics/IVChart"
import { StrategySuggestions } from "@/components/dashboard/StrategySuggestions"
import { useIVAnalysis, useMarketSentiment } from "@/hooks/useMarketData"
import { TrendingUp, TrendingDown, Minus, Activity, BarChart3 } from "lucide-react"
import type { Market, Sentiment } from "@/lib/api"

interface SymbolOverviewProps {
  symbol: string
  market: Market
}

const SENTIMENT_CONFIG: Record<Sentiment, { label: string; color: string; icon: typeof TrendingUp }> = {
  bullish:          { label: "BULLISH",   color: "text-bb-green", icon: TrendingUp },
  slightly_bullish: { label: "SL. BULLISH", color: "text-bb-green", icon: TrendingUp },
  neutral:          { label: "NEUTRAL",   color: "text-bb-amber", icon: Minus },
  slightly_bearish: { label: "SL. BEARISH", color: "text-bb-red",   icon: TrendingDown },
  bearish:          { label: "BEARISH",   color: "text-bb-red",   icon: TrendingDown },
}

function IVRankBar({ value, label }: { value: number; label: string }) {
  const pct = Math.min(100, Math.max(0, value))
  const barColor = pct > 70 ? "bg-bb-red" : pct > 30 ? "bg-bb-amber" : "bg-bb-green"

  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-muted-foreground uppercase">{label}</span>
        <span className="font-semibold tabular-nums">{value.toFixed(0)}</span>
      </div>
      <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function IVAnalysisCard({ symbol, market }: { symbol: string; market: Market }) {
  const { data: iv, isLoading } = useIVAnalysis(symbol, market)

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader className="py-2 px-3">
          <CardTitle className="text-xs flex items-center gap-1.5">
            <Activity className="h-3.5 w-3.5 text-primary" />
            IV Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="h-6 bg-muted rounded" />)}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!iv) return null

  return (
    <Card className="h-full">
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs flex items-center gap-1.5">
          <Activity className="h-3.5 w-3.5 text-primary" />
          IV Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="px-3 pb-3 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Current IV</span>
          <span className="font-bold text-bb-cyan tabular-nums">{(iv.current_iv * 100).toFixed(1)}%</span>
        </div>
        <IVRankBar value={iv.iv_rank} label="IV Rank" />
        <IVRankBar value={iv.iv_percentile} label="IV Percentile" />
        <div className="border-t border-border pt-2 mt-2 space-y-1">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-muted-foreground">52w Range</span>
            <span className="tabular-nums">
              {(iv.iv_52w_low * 100).toFixed(1)}% — {(iv.iv_52w_high * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-muted-foreground">30d Avg</span>
            <span className="tabular-nums">{(iv.iv_30d_avg * 100).toFixed(1)}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SentimentCard({ symbol, market }: { symbol: string; market: Market }) {
  const { data: sentiment, isLoading } = useMarketSentiment(symbol, market)

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader className="py-2 px-3">
          <CardTitle className="text-xs flex items-center gap-1.5">
            <BarChart3 className="h-3.5 w-3.5 text-primary" />
            Sentiment
          </CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <div className="animate-pulse space-y-2">
            {[1, 2, 3].map(i => <div key={i} className="h-6 bg-muted rounded" />)}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!sentiment) return null

  const config = SENTIMENT_CONFIG[sentiment.sentiment]
  const SentimentIcon = config.icon

  return (
    <Card className="h-full">
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs flex items-center gap-1.5">
          <BarChart3 className="h-3.5 w-3.5 text-primary" />
          Sentiment
        </CardTitle>
      </CardHeader>
      <CardContent className="px-3 pb-3 space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">P/C Ratio</span>
          <span className="font-bold tabular-nums">{sentiment.put_call_ratio.toFixed(2)}</span>
        </div>
        <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[10px]">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Call Vol</span>
            <span className="tabular-nums">
              {sentiment.total_call_volume >= 1e6
                ? `${(sentiment.total_call_volume / 1e6).toFixed(1)}M`
                : `${(sentiment.total_call_volume / 1e3).toFixed(0)}K`}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Put Vol</span>
            <span className="tabular-nums">
              {sentiment.total_put_volume >= 1e6
                ? `${(sentiment.total_put_volume / 1e6).toFixed(1)}M`
                : `${(sentiment.total_put_volume / 1e3).toFixed(0)}K`}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Call OI</span>
            <span className="tabular-nums">
              {sentiment.call_open_interest >= 1e6
                ? `${(sentiment.call_open_interest / 1e6).toFixed(1)}M`
                : `${(sentiment.call_open_interest / 1e3).toFixed(0)}K`}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Put OI</span>
            <span className="tabular-nums">
              {sentiment.put_open_interest >= 1e6
                ? `${(sentiment.put_open_interest / 1e6).toFixed(1)}M`
                : `${(sentiment.put_open_interest / 1e3).toFixed(0)}K`}
            </span>
          </div>
        </div>
        <div className="border-t border-border pt-2 mt-1">
          <div className="flex items-center gap-1.5">
            <SentimentIcon className={`h-3.5 w-3.5 ${config.color}`} />
            <span className={`text-xs font-bold ${config.color}`}>{config.label}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function SymbolOverview({ symbol, market }: SymbolOverviewProps) {
  return (
    <div className="space-y-3">
      {/* Top row: PriceChart (2/3) + IV & Sentiment cards (1/3) */}
      <div className="grid grid-cols-3 gap-3">
        <div className="col-span-2">
          <PriceChart symbol={symbol} market={market} />
        </div>
        <div className="space-y-3">
          <IVAnalysisCard symbol={symbol} market={market} />
          <SentimentCard symbol={symbol} market={market} />
        </div>
      </div>

      {/* IV History (full width) */}
      <IVChart symbol={symbol} market={market} />

      {/* Strategy Suggestions (full width) */}
      <StrategySuggestions symbol={symbol} market={market} />
    </div>
  )
}
