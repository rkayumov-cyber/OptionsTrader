import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Activity, TrendingUp, TrendingDown } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Area, ComposedChart } from "recharts"
import { useIVHistory } from "@/hooks/useMarketData"
import type { Market } from "@/lib/api"

interface IVChartProps {
  symbol?: string
  market?: Market
  className?: string
}

export function IVChart({
  symbol: initialSymbol = "AAPL",
  market: initialMarket = "US",
  className
}: IVChartProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<Market>(initialMarket)
  const [days, setDays] = useState(90)

  const { data, isLoading } = useIVHistory(symbol, market, days)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">IV History</CardTitle>
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
            <Activity className="h-4 w-4" />
            IV History
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="w-24 h-8"
            />
            <Select
              value={market}
              onChange={(e) => setMarket(e.target.value as Market)}
              className="w-20 h-8"
            >
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="HK">HK</option>
            </Select>
            <Select
              value={days.toString()}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="w-24 h-8"
            >
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
              <option value="180">180 days</option>
            </Select>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data && (
          <>
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Current IV</div>
                <span className="text-lg font-bold tabular-nums">{data.current_iv?.toFixed(1) ?? "—"}%</span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">IV Rank</div>
                <span className={`text-lg font-bold tabular-nums ${(data.current_iv_rank ?? 0) > 50 ? "text-bb-amber" : "text-bb-blue"}`}>
                  {data.current_iv_rank?.toFixed(1) ?? "—"}%
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                  <TrendingUp className="h-3.5 w-3.5" />
                  52w High
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-red">{data.iv_52w_high?.toFixed(1) ?? "—"}%</span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                  <TrendingDown className="h-3.5 w-3.5" />
                  52w Low
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-green">{data.iv_52w_low?.toFixed(1) ?? "—"}%</span>
              </div>
            </div>

            {/* Chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data.history} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(v) => new Date(v).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  />
                  <YAxis yAxisId="iv" orientation="left" tickFormatter={(v) => `${v}%`} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                  <YAxis yAxisId="price" orientation="right" tickFormatter={(v) => `$${v}`} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      name === "price" ? `$${value.toFixed(2)}` : `${value.toFixed(1)}%`,
                      name === "price" ? "Price" : name === "iv" ? "IV" : "IV Rank"
                    ]}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                  />
                  <Legend />
                  <Area
                    yAxisId="iv"
                    type="monotone"
                    dataKey="iv"
                    stroke="hsl(var(--bb-blue))"
                    fill="hsl(var(--bb-blue))"
                    fillOpacity={0.2}
                    name="IV"
                  />
                  <Line
                    yAxisId="iv"
                    type="monotone"
                    dataKey="iv_rank"
                    stroke="hsl(var(--bb-amber))"
                    strokeWidth={2}
                    dot={false}
                    name="IV Rank"
                  />
                  <Line
                    yAxisId="price"
                    type="monotone"
                    dataKey="price"
                    stroke="hsl(var(--bb-green))"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Price"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
