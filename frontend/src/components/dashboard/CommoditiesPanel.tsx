import { useMarketIndicators } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, TrendingDown } from "lucide-react"
import { cn } from "@/lib/utils"

interface CommoditiesPanelProps {
  className?: string
}

interface CommodityRowProps {
  symbol: string
  name: string
  price: number
  change: number | null
  changePercent: number | null
  prefix?: string
}

function CommodityRow({ symbol, name, price, changePercent, prefix = "$" }: CommodityRowProps) {
  const isPositive = (changePercent ?? 0) >= 0

  return (
    <div className="flex items-center justify-between py-1.5">
      <div className="flex items-center gap-2">
        <span className="text-xs font-semibold text-bb-cyan">{symbol}</span>
        <span className="text-[10px] text-muted-foreground">{name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm font-bold tabular-nums">
          {prefix}{price.toFixed(2)}
        </span>
        {changePercent !== null && (
          <span
            className={cn(
              "flex items-center text-xs tabular-nums min-w-[60px] justify-end",
              isPositive ? "text-bb-green" : "text-destructive"
            )}
          >
            {isPositive ? (
              <TrendingUp className="h-3 w-3 mr-0.5" />
            ) : (
              <TrendingDown className="h-3 w-3 mr-0.5" />
            )}
            {isPositive ? "+" : ""}{changePercent.toFixed(2)}%
          </span>
        )}
      </div>
    </div>
  )
}

export function CommoditiesPanel({ className }: CommoditiesPanelProps) {
  const { data, isLoading } = useMarketIndicators()

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">COMMODITIES</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const commodities = data?.commodities
  if (!commodities) return null

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">COMMODITIES</CardTitle>
      </CardHeader>
      <CardContent className="space-y-0 divide-y divide-border">
        <CommodityRow
          symbol="GLD"
          name="Gold"
          price={commodities.gold_price}
          change={commodities.gold_change}
          changePercent={commodities.gold_change_percent}
        />
        <CommodityRow
          symbol="USO"
          name="Crude Oil"
          price={commodities.oil_price}
          change={commodities.oil_change}
          changePercent={commodities.oil_change_percent}
        />
        <CommodityRow
          symbol="UUP"
          name="US Dollar"
          price={commodities.dollar_price}
          change={commodities.dollar_change}
          changePercent={commodities.dollar_change_percent}
        />
      </CardContent>
    </Card>
  )
}
