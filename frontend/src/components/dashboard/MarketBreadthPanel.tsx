import { useMarketIndicators } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface MarketBreadthPanelProps {
  className?: string
}

function BreadthBar({
  label,
  leftValue,
  rightValue,
  leftLabel,
  rightLabel
}: {
  label: string
  leftValue: number
  rightValue: number
  leftLabel: string
  rightLabel: string
}) {
  const total = leftValue + rightValue
  const leftPercent = total > 0 ? (leftValue / total) * 100 : 50
  const rightPercent = total > 0 ? (rightValue / total) * 100 : 50

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>{leftLabel}: {leftValue}</span>
        <span className="font-medium">{label}</span>
        <span>{rightLabel}: {rightValue}</span>
      </div>
      <div className="flex h-2 rounded overflow-hidden">
        <div
          className="bg-bb-green transition-all"
          style={{ width: `${leftPercent}%` }}
        />
        <div
          className="bg-destructive transition-all"
          style={{ width: `${rightPercent}%` }}
        />
      </div>
    </div>
  )
}

export function MarketBreadthPanel({ className }: MarketBreadthPanelProps) {
  const { data, isLoading } = useMarketIndicators()

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">MARKET BREADTH</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const breadth = data?.breadth
  if (!breadth) return null

  const adRatio = breadth.advance_decline_ratio
  const hlRatio = breadth.highs_lows_ratio
  const mcclellan = breadth.mcclellan_oscillator

  const adBullish = adRatio >= 1
  const hlBullish = hlRatio >= 1
  const mcclellanBullish = mcclellan !== null && mcclellan >= 0

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">MARKET BREADTH</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Advance/Decline */}
        <BreadthBar
          label="A/D"
          leftValue={breadth.advances}
          rightValue={breadth.declines}
          leftLabel="Adv"
          rightLabel="Dec"
        />

        {/* New Highs/Lows */}
        <BreadthBar
          label="H/L"
          leftValue={breadth.new_highs}
          rightValue={breadth.new_lows}
          leftLabel="Highs"
          rightLabel="Lows"
        />

        {/* Ratios Summary */}
        <div className="grid grid-cols-2 gap-2 pt-1 border-t border-border">
          <div className="text-center">
            <div className="text-[10px] text-muted-foreground uppercase">A/D Ratio</div>
            <div className={cn(
              "text-sm font-bold tabular-nums flex items-center justify-center gap-1",
              adBullish ? "text-bb-green" : "text-destructive"
            )}>
              {adBullish ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {adRatio.toFixed(2)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-muted-foreground uppercase">H/L Ratio</div>
            <div className={cn(
              "text-sm font-bold tabular-nums flex items-center justify-center gap-1",
              hlBullish ? "text-bb-green" : "text-destructive"
            )}>
              {hlBullish ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {hlRatio.toFixed(2)}
            </div>
          </div>
        </div>

        {/* McClellan Oscillator */}
        {mcclellan !== null && (
          <div className="flex items-center justify-between pt-1 border-t border-border">
            <span className="text-[10px] text-muted-foreground uppercase">McClellan Osc</span>
            <span className={cn(
              "text-sm font-bold tabular-nums flex items-center gap-1",
              mcclellanBullish ? "text-bb-green" : "text-destructive"
            )}>
              {mcclellanBullish ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {mcclellan >= 0 ? "+" : ""}{mcclellan.toFixed(1)}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
