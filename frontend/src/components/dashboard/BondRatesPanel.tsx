import { useMarketIndicators } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react"
import { cn } from "@/lib/utils"

interface BondRatesPanelProps {
  className?: string
}

export function BondRatesPanel({ className }: BondRatesPanelProps) {
  const { data, isLoading } = useMarketIndicators()

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">BONDS / RATES</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const bonds = data?.bonds
  if (!bonds) return null

  const yieldSpread = bonds.yield_spread
  const isInverted = yieldSpread < 0

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          BONDS / RATES
          {isInverted && (
            <span className="flex items-center gap-1 text-[10px] text-destructive">
              <AlertTriangle className="h-3 w-3" />
              INVERTED
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {/* Treasury Yields */}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-0.5">
            <div className="text-[10px] text-muted-foreground uppercase">10Y Treasury</div>
            <div className="text-lg font-bold tabular-nums text-bb-cyan">
              {bonds.tnx_yield.toFixed(2)}%
            </div>
          </div>
          <div className="space-y-0.5">
            <div className="text-[10px] text-muted-foreground uppercase">2Y Treasury</div>
            <div className="text-lg font-bold tabular-nums text-bb-cyan">
              {bonds.irx_yield.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Yield Spread */}
        <div className="flex items-center justify-between py-1 px-2 rounded bg-muted/30">
          <span className="text-[10px] text-muted-foreground uppercase">10Y-2Y Spread</span>
          <span
            className={cn(
              "text-sm font-bold tabular-nums",
              isInverted ? "text-destructive" : "text-bb-green"
            )}
          >
            {yieldSpread > 0 ? "+" : ""}{(yieldSpread * 100).toFixed(0)} bps
          </span>
        </div>

        {/* TLT */}
        <div className="flex items-center justify-between pt-1 border-t border-border">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium">TLT</span>
            <span className="text-[10px] text-muted-foreground">20+ Yr Treasury</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold tabular-nums">
              ${bonds.tlt_price.toFixed(2)}
            </span>
            {bonds.tlt_change_percent !== null && (
              <span
                className={cn(
                  "flex items-center text-xs tabular-nums",
                  bonds.tlt_change_percent >= 0 ? "text-bb-green" : "text-destructive"
                )}
              >
                {bonds.tlt_change_percent >= 0 ? (
                  <TrendingUp className="h-3 w-3 mr-0.5" />
                ) : (
                  <TrendingDown className="h-3 w-3 mr-0.5" />
                )}
                {bonds.tlt_change_percent >= 0 ? "+" : ""}
                {bonds.tlt_change_percent.toFixed(2)}%
              </span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
