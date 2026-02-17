import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, BarChart3, TrendingUp, TrendingDown } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from "recharts"
import { useSkewAnalysis } from "@/hooks/useMarketData"
import type { Market } from "@/lib/api"

interface SkewChartProps {
  symbol?: string
  market?: Market
  className?: string
}

export function SkewChart({
  symbol: initialSymbol = "AAPL",
  market: initialMarket = "US",
  className
}: SkewChartProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<Market>(initialMarket)

  const { data, isLoading } = useSkewAnalysis(symbol, market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Volatility Skew</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const formatMoneyness = (value: number) => {
    if (value === 1) return "ATM"
    return value < 1 ? `${((1 - value) * 100).toFixed(0)}% OTM` : `${((value - 1) * 100).toFixed(0)}% ITM`
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Volatility Skew
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
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {data && (
          <>
            {/* Skew Summary */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Underlying</div>
                <span className="text-lg font-bold tabular-nums">${data.underlying_price.toFixed(2)}</span>
              </div>
              <div className="bg-bb-red/10 border border-bb-red/20 rounded-lg p-3">
                <div className="flex items-center gap-1 text-bb-red text-[10px] uppercase tracking-wider mb-1">
                  <TrendingDown className="h-3.5 w-3.5" />
                  Put Skew Index
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-red">{data.put_skew_index.toFixed(2)}</span>
              </div>
              <div className="bg-bb-green/10 border border-bb-green/20 rounded-lg p-3">
                <div className="flex items-center gap-1 text-bb-green text-[10px] uppercase tracking-wider mb-1">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Call Skew Index
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-green">{data.call_skew_index.toFixed(2)}</span>
              </div>
            </div>

            {/* Chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.skew_data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="strike"
                    tickFormatter={(v) => `$${v}`}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                  />
                  <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} domain={['auto', 'auto']} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)}%`,
                      name === "call_iv" ? "Call IV" : name === "put_iv" ? "Put IV" : "Skew"
                    ]}
                    labelFormatter={(label) => `Strike: $${label}`}
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                  />
                  <Legend />
                  <ReferenceLine x={data.underlying_price} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" label="ATM" />
                  <Line
                    type="monotone"
                    dataKey="put_iv"
                    stroke="hsl(var(--bb-red))"
                    strokeWidth={2}
                    dot={false}
                    name="Put IV"
                  />
                  <Line
                    type="monotone"
                    dataKey="call_iv"
                    stroke="hsl(var(--bb-green))"
                    strokeWidth={2}
                    dot={false}
                    name="Call IV"
                  />
                  <Line
                    type="monotone"
                    dataKey="skew"
                    stroke="hsl(var(--bb-cyan))"
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Skew (Put-Call)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Interpretation */}
            <div className="bg-muted/30 rounded-lg p-3 text-xs">
              <p className="font-semibold mb-1">Skew Interpretation:</p>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li>
                  Put skew index of {data.put_skew_index.toFixed(2)} indicates {data.put_skew_index > 1.05 ? "elevated downside protection demand" : data.put_skew_index < 0.95 ? "low downside concern" : "normal put skew"}
                </li>
                <li>
                  Call skew index of {data.call_skew_index.toFixed(2)} indicates {data.call_skew_index > 1.05 ? "elevated upside demand" : data.call_skew_index < 0.95 ? "limited upside expectations" : "normal call skew"}
                </li>
              </ul>
            </div>

            <p className="text-xs text-muted-foreground text-center">
              Expiration: {new Date(data.expiration).toLocaleDateString()}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}
