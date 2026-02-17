import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Calendar, Sun, Moon, Clock, TrendingDown } from "lucide-react"
import { useEarningsCalendar } from "@/hooks/useMarketData"
import type { EarningsEvent } from "@/lib/api"

interface EarningsCalendarProps {
  watchlistSymbols?: string[]
  className?: string
}

const TIME_ICONS: Record<string, React.ReactNode> = {
  before_open: <Sun className="h-3.5 w-3.5 text-bb-amber" />,
  after_close: <Moon className="h-3.5 w-3.5 text-bb-blue" />,
  during_market: <Clock className="h-3.5 w-3.5 text-bb-green" />,
  unknown: <Clock className="h-3.5 w-3.5 text-muted-foreground" />,
}

const TIME_LABELS: Record<string, string> = {
  before_open: "BMO",
  after_close: "AMC",
  during_market: "During",
  unknown: "TBD",
}

export function EarningsCalendar({ watchlistSymbols, className }: EarningsCalendarProps) {
  const [days, setDays] = useState(30)
  const [symbolFilter, setSymbolFilter] = useState("")

  const { data, isLoading } = useEarningsCalendar(watchlistSymbols, days)

  const filteredEvents = data?.events.filter(event =>
    !symbolFilter || event.symbol.toLowerCase().includes(symbolFilter.toLowerCase())
  ) || []

  // Group events by date
  const eventsByDate = filteredEvents.reduce((acc, event) => {
    const date = event.earnings_date.split("T")[0]
    if (!acc[date]) acc[date] = []
    acc[date].push(event)
    return acc
  }, {} as Record<string, EarningsEvent[]>)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Earnings Calendar</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Earnings Calendar
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Filter symbol"
              value={symbolFilter}
              onChange={(e) => setSymbolFilter(e.target.value.toUpperCase())}
              className="w-28 h-8"
            />
            <Select
              value={days.toString()}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-24 h-8"
            >
              <option value="7">7 days</option>
              <option value="14">14 days</option>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
            </Select>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.keys(eventsByDate).length > 0 ? (
          <div className="space-y-4 max-h-[480px] overflow-y-auto">
            {Object.entries(eventsByDate).sort(([a], [b]) => a.localeCompare(b)).map(([date, events]) => (
              <div key={date}>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-semibold">
                    {new Date(date).toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
                  </span>
                  <span className="text-xs text-muted-foreground">({events.length} events)</span>
                </div>
                <div className="space-y-2 pl-4 border-l-2 border-muted">
                  {events.map((event, i) => (
                    <div key={`${event.symbol}-${i}`} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold">{event.symbol}</span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{event.market}</span>
                          <div className="flex items-center gap-1 text-xs">
                            {TIME_ICONS[event.time_of_day]}
                            <span>{TIME_LABELS[event.time_of_day]}</span>
                          </div>
                        </div>
                        {event.iv_crush_percent != null && (
                          <div className="flex items-center gap-1 text-xs">
                            <TrendingDown className="h-3.5 w-3.5 text-bb-amber" />
                            <span className="text-bb-amber">IV Crush: {event.iv_crush_percent.toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{event.company_name}</p>
                      {(event.estimated_eps != null || event.actual_eps != null) && (
                        <div className="flex gap-4 mt-2 text-xs">
                          {event.estimated_eps != null && (
                            <span className="tabular-nums">Est EPS: ${event.estimated_eps.toFixed(2)}</span>
                          )}
                          {event.actual_eps != null && (
                            <span className={`tabular-nums ${event.surprise_percent && event.surprise_percent > 0 ? "text-bb-green" : "text-bb-red"}`}>
                              Actual: ${event.actual_eps.toFixed(2)}
                              {event.surprise_percent != null && ` (${event.surprise_percent > 0 ? "+" : ""}${event.surprise_percent.toFixed(1)}%)`}
                            </span>
                          )}
                        </div>
                      )}
                      {(event.iv_before != null || event.iv_after != null) && (
                        <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                          {event.iv_before != null && <span className="tabular-nums">IV Before: {event.iv_before.toFixed(1)}%</span>}
                          {event.iv_after != null && <span className="tabular-nums">IV After: {event.iv_after.toFixed(1)}%</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Calendar className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No upcoming earnings</p>
            <p className="text-xs text-muted-foreground mt-1">Try extending the date range</p>
          </div>
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground pt-2 border-t">
          <div className="flex items-center gap-1">
            <Sun className="h-3.5 w-3.5 text-bb-amber" />
            <span>Before Market Open</span>
          </div>
          <div className="flex items-center gap-1">
            <Moon className="h-3.5 w-3.5 text-bb-blue" />
            <span>After Market Close</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
