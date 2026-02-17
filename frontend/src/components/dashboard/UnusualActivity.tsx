import { useUnusualActivity } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, Activity, BarChart3, AlertTriangle } from "lucide-react"
import type { Market, AlertType } from "@/lib/api"

interface UnusualActivityProps {
  market?: Market
  onSymbolSelect?: (symbol: string, market: Market) => void
  className?: string
}

const getAlertIcon = (type: AlertType) => {
  switch (type) {
    case "volume_spike":
      return <TrendingUp className="h-3.5 w-3.5" />
    case "unusual_pc_ratio":
      return <BarChart3 className="h-3.5 w-3.5" />
    case "oi_change":
      return <Activity className="h-3.5 w-3.5" />
    default:
      return <AlertTriangle className="h-3.5 w-3.5" />
  }
}

const getAlertColorVar = (type: AlertType) => {
  switch (type) {
    case "volume_spike":
      return "var(--bb-green)"
    case "unusual_pc_ratio":
      return "var(--bb-blue)"
    case "oi_change":
      return "var(--bb-amber)"
    default:
      return "var(--bb-muted)"
  }
}

const getSignificanceColorVar = (significance: number) => {
  if (significance >= 8) return "var(--bb-red)"
  if (significance >= 6) return "var(--bb-orange)"
  return "var(--bb-amber)"
}

const formatTimeAgo = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMinutes = Math.floor((now.getTime() - time.getTime()) / 60000)

  if (diffMinutes < 1) return "Just now"
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`
  return `${Math.floor(diffMinutes / 1440)}d ago`
}

export function UnusualActivity({
  market,
  onSymbolSelect,
  className,
}: UnusualActivityProps) {
  const { data, isLoading } = useUnusualActivity(market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-bb-amber" />
            Unusual Activity
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const alerts = data?.alerts || []

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-bb-amber" />
          Unusual Activity
          {alerts.length > 0 && (
            <span className="text-[10px] bg-bb-amber/20 text-bb-amber px-1.5 py-0.5 rounded-full">
              {alerts.length}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <AlertTriangle className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No unusual activity detected</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[480px] overflow-y-auto">
            {alerts.map((alert, index) => (
              <button
                key={`${alert.symbol}-${alert.alert_type}-${index}`}
                onClick={() => onSymbolSelect?.(alert.symbol, alert.market)}
                className="w-full text-left border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div
                      className="p-1.5 rounded-md"
                      style={{
                        backgroundColor: `hsl(${getAlertColorVar(alert.alert_type)} / 0.13)`,
                        color: `hsl(${getAlertColorVar(alert.alert_type)})`,
                      }}
                    >
                      {getAlertIcon(alert.alert_type)}
                    </div>
                    <div>
                      <div className="font-medium text-sm">
                        {alert.symbol}
                        <span className="text-xs text-muted-foreground ml-1">
                          ({alert.market})
                        </span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {alert.description}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div
                      className="text-[10px] font-medium px-1.5 py-0.5 rounded-full tabular-nums"
                      style={{
                        backgroundColor: `hsl(${getSignificanceColorVar(alert.significance)} / 0.13)`,
                        color: `hsl(${getSignificanceColorVar(alert.significance)})`,
                      }}
                    >
                      {alert.significance.toFixed(1)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatTimeAgo(alert.timestamp)}
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
