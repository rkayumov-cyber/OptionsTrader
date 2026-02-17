import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Calendar, AlertCircle } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { useTermStructure } from "@/hooks/useMarketData"
import type { Market } from "@/lib/api"

interface TermStructureProps {
  symbol?: string
  market?: Market
  className?: string
}

export function TermStructure({
  symbol: initialSymbol = "AAPL",
  market: initialMarket = "US",
  className
}: TermStructureProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market, setMarket] = useState<Market>(initialMarket)

  const { data, isLoading } = useTermStructure(symbol, market)

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Term Structure</CardTitle>
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
            Term Structure
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
            {/* Contango/Backwardation Indicator */}
            <div className={`flex items-center gap-2 p-3 rounded-lg ${data.contango ? "bg-bb-amber/10 border border-bb-amber/20" : "bg-bb-blue/10 border border-bb-blue/20"}`}>
              <AlertCircle className={`h-4 w-4 ${data.contango ? "text-bb-amber" : "text-bb-blue"}`} />
              <div>
                <span className={`font-semibold ${data.contango ? "text-bb-amber" : "text-bb-blue"}`}>
                  {data.contango ? "Contango" : "Backwardation"}
                </span>
                <p className="text-xs text-muted-foreground">
                  {data.contango
                    ? "Far-dated IV is higher than near-dated - normal market conditions"
                    : "Near-dated IV is higher than far-dated - potential near-term uncertainty"}
                </p>
              </div>
            </div>

            {/* Chart */}
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.structure} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis
                    dataKey="dte"
                    tickFormatter={(v) => `${v}d`}
                    tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }}
                    label={{ value: "Days to Expiration", position: "insideBottom", offset: -5 }}
                  />
                  <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                  <Tooltip
                    formatter={(value: number, name: string) => [
                      `${value.toFixed(1)}%`,
                      name === "iv" ? "ATM IV" : name === "call_iv" ? "Call IV" : "Put IV"
                    ]}
                    labelFormatter={(label) => `${label} DTE`}
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="iv"
                    stroke="hsl(var(--bb-blue))"
                    strokeWidth={3}
                    dot={{ fill: "hsl(var(--bb-blue))", r: 4 }}
                    name="ATM IV"
                  />
                  <Line
                    type="monotone"
                    dataKey="call_iv"
                    stroke="hsl(var(--bb-green))"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Call IV"
                  />
                  <Line
                    type="monotone"
                    dataKey="put_iv"
                    stroke="hsl(var(--bb-red))"
                    strokeWidth={1}
                    strokeDasharray="3 3"
                    dot={false}
                    name="Put IV"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Expiration Details */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Expiration</th>
                    <th className="text-right py-2">DTE</th>
                    <th className="text-right py-2">ATM IV</th>
                    <th className="text-right py-2">Call IV</th>
                    <th className="text-right py-2">Put IV</th>
                  </tr>
                </thead>
                <tbody>
                  {data.structure.map((point, i) => (
                    <tr key={i} className="border-b border-muted">
                      <td className="py-2">{new Date(point.expiration).toLocaleDateString()}</td>
                      <td className="text-right py-2 tabular-nums">{point.dte}</td>
                      <td className="text-right py-2 font-semibold tabular-nums">{point.iv.toFixed(1)}%</td>
                      <td className="text-right py-2 text-bb-green tabular-nums">{point.call_iv.toFixed(1)}%</td>
                      <td className="text-right py-2 text-bb-red tabular-nums">{point.put_iv.toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
