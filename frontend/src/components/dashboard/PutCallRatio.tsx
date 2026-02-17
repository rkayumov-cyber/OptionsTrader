import { useMarketSentiment } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import type { Market, Sentiment } from "@/lib/api"

interface PutCallRatioProps {
  symbol: string
  market: Market
  className?: string
}

const formatVolume = (volume: number): string => {
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(0)}K`
  return volume.toString()
}

const getSentimentConfig = (sentiment: Sentiment) => {
  const configs: Record<Sentiment, { label: string; colorVar: string }> = {
    bullish: { label: "Bullish", colorVar: "var(--bb-green)" },
    slightly_bullish: { label: "Slightly Bullish", colorVar: "var(--bb-green)" },
    neutral: { label: "Neutral", colorVar: "var(--bb-amber)" },
    slightly_bearish: { label: "Slightly Bearish", colorVar: "var(--bb-orange)" },
    bearish: { label: "Bearish", colorVar: "var(--bb-red)" },
  }
  return configs[sentiment]
}

export function PutCallRatio({ symbol, market, className }: PutCallRatioProps) {
  const { data: sentiment, isLoading } = useMarketSentiment(symbol, market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Put/Call Ratio</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (!sentiment) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Put/Call Ratio</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32 text-muted-foreground">
          No data available
        </CardContent>
      </Card>
    )
  }

  const sentimentConfig = getSentimentConfig(sentiment.sentiment)
  const totalVolume = sentiment.total_call_volume + sentiment.total_put_volume
  const callPercent = (sentiment.total_call_volume / totalVolume) * 100
  const putPercent = (sentiment.total_put_volume / totalVolume) * 100

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Put/Call Ratio</span>
          <span className="text-sm font-normal text-muted-foreground">{symbol}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main ratio display */}
        <div className="flex items-center justify-between">
          <div
            className="text-3xl font-bold tabular-nums"
            style={{ color: `hsl(${sentimentConfig.colorVar})` }}
          >
            {sentiment.put_call_ratio.toFixed(2)}
          </div>
          <div
            className="px-3 py-1 rounded-full text-sm font-medium"
            style={{
              backgroundColor: `hsl(${sentimentConfig.colorVar} / 0.13)`,
              color: `hsl(${sentimentConfig.colorVar})`,
            }}
          >
            {sentimentConfig.label}
          </div>
        </div>

        {/* Horizontal bar */}
        <div className="space-y-1">
          <div className="flex h-4 rounded-full overflow-hidden bg-muted">
            <div
              className="bg-bb-green transition-all duration-300"
              style={{ width: `${callPercent}%` }}
            />
            <div
              className="bg-bb-red transition-all duration-300"
              style={{ width: `${putPercent}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span className="text-bb-green tabular-nums">
              Calls: {formatVolume(sentiment.total_call_volume)} ({callPercent.toFixed(0)}%)
            </span>
            <span className="text-bb-red tabular-nums">
              Puts: {formatVolume(sentiment.total_put_volume)} ({putPercent.toFixed(0)}%)
            </span>
          </div>
        </div>

        {/* Open Interest */}
        <div className="grid grid-cols-2 gap-2 pt-2 border-t text-xs">
          <div>
            <span className="text-muted-foreground">Call OI: </span>
            <span className="text-bb-green tabular-nums">{formatVolume(sentiment.call_open_interest)}</span>
          </div>
          <div className="text-right">
            <span className="text-muted-foreground">Put OI: </span>
            <span className="text-bb-red tabular-nums">{formatVolume(sentiment.put_open_interest)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
