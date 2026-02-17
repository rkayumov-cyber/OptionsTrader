import { useState, useMemo, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Plus, Trash2, TrendingUp, TrendingDown, DollarSign, Clock } from "lucide-react"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Legend } from "recharts"
import { useCalculatePayoff, useCalculateTimeSeriesPayoff } from "@/hooks/useMarketData"
import type { PayoffLeg, PayoffResult, OptionType, ActionType, TimeSeriesPayoffResult } from "@/lib/api"

interface PayoffDiagramProps {
  initialPrice?: number
  className?: string
}

const TIME_CURVE_COLORS = [
  "hsl(var(--bb-blue))",
  "hsl(var(--bb-green))",
  "hsl(var(--bb-amber))",
  "hsl(var(--bb-cyan))",
  "hsl(var(--bb-red))",
]

export function PayoffDiagram({ initialPrice = 100, className }: PayoffDiagramProps) {
  const [underlyingPrice, setUnderlyingPrice] = useState(initialPrice)
  const [legs, setLegs] = useState<PayoffLeg[]>([])
  const [payoffResult, setPayoffResult] = useState<PayoffResult | null>(null)
  const [timeSeriesResult, setTimeSeriesResult] = useState<TimeSeriesPayoffResult | null>(null)
  const [selectedStrategy, setSelectedStrategy] = useState<string>("")
  const [showTimeDecay, setShowTimeDecay] = useState(false)
  const [maxDTE, setMaxDTE] = useState(30)
  const [iv, setIV] = useState(30)
  const [selectedDTE, setSelectedDTE] = useState<number | null>(null)

  const calculatePayoff = useCalculatePayoff()
  const calculateTimeSeries = useCalculateTimeSeriesPayoff()

  // Auto-calculate when legs change
  useEffect(() => {
    if (legs.length > 0 && underlyingPrice > 0) {
      if (showTimeDecay) {
        calculateTimeSeries.mutate(
          {
            legs,
            underlying_price: underlyingPrice,
            max_dte: maxDTE,
            iv: iv / 100,
            num_points: 50,
          },
          { onSuccess: setTimeSeriesResult }
        )
      } else {
        calculatePayoff.mutate(
          { legs, underlying_price: underlyingPrice },
          { onSuccess: setPayoffResult }
        )
      }
    } else {
      setPayoffResult(null)
      setTimeSeriesResult(null)
    }
  }, [legs, underlyingPrice, showTimeDecay, maxDTE, iv])

  const addLeg = () => {
    const newLeg: PayoffLeg = {
      option_type: "call",
      action: "buy",
      strike: underlyingPrice,
      quantity: 1,
      premium: 5,
    }
    setLegs([...legs, newLeg])
  }

  const updateLeg = (index: number, updates: Partial<PayoffLeg>) => {
    const newLegs = [...legs]
    newLegs[index] = { ...newLegs[index], ...updates }
    setLegs(newLegs)
  }

  const removeLeg = (index: number) => {
    setLegs(legs.filter((_, i) => i !== index))
  }

  const applyStrategy = (strategyName: string) => {
    const strategyLegs: Record<string, PayoffLeg[]> = {
      long_call: [{ option_type: "call", action: "buy", strike: underlyingPrice, quantity: 1, premium: 5 }],
      long_put: [{ option_type: "put", action: "buy", strike: underlyingPrice, quantity: 1, premium: 5 }],
      covered_call: [
        { option_type: "call", action: "sell", strike: underlyingPrice * 1.05, quantity: 1, premium: 3 },
      ],
      bull_call_spread: [
        { option_type: "call", action: "buy", strike: underlyingPrice * 0.95, quantity: 1, premium: 8 },
        { option_type: "call", action: "sell", strike: underlyingPrice * 1.05, quantity: 1, premium: 3 },
      ],
      bear_put_spread: [
        { option_type: "put", action: "buy", strike: underlyingPrice * 1.05, quantity: 1, premium: 8 },
        { option_type: "put", action: "sell", strike: underlyingPrice * 0.95, quantity: 1, premium: 3 },
      ],
      straddle: [
        { option_type: "call", action: "buy", strike: underlyingPrice, quantity: 1, premium: 5 },
        { option_type: "put", action: "buy", strike: underlyingPrice, quantity: 1, premium: 5 },
      ],
      strangle: [
        { option_type: "call", action: "buy", strike: underlyingPrice * 1.05, quantity: 1, premium: 3 },
        { option_type: "put", action: "buy", strike: underlyingPrice * 0.95, quantity: 1, premium: 3 },
      ],
      iron_condor: [
        { option_type: "put", action: "buy", strike: underlyingPrice * 0.9, quantity: 1, premium: 2 },
        { option_type: "put", action: "sell", strike: underlyingPrice * 0.95, quantity: 1, premium: 4 },
        { option_type: "call", action: "sell", strike: underlyingPrice * 1.05, quantity: 1, premium: 4 },
        { option_type: "call", action: "buy", strike: underlyingPrice * 1.1, quantity: 1, premium: 2 },
      ],
      butterfly: [
        { option_type: "call", action: "buy", strike: underlyingPrice * 0.95, quantity: 1, premium: 8 },
        { option_type: "call", action: "sell", strike: underlyingPrice, quantity: 2, premium: 5 },
        { option_type: "call", action: "buy", strike: underlyingPrice * 1.05, quantity: 1, premium: 3 },
      ],
    }

    if (strategyLegs[strategyName]) {
      setLegs(strategyLegs[strategyName].map(leg => ({
        ...leg,
        strike: Math.round(leg.strike * 100) / 100,
      })))
      setSelectedStrategy(strategyName)
    }
  }

  // Chart data for standard payoff
  const chartData = useMemo(() => {
    if (!payoffResult) return []
    return payoffResult.points.map(point => ({
      price: point.price,
      pnl: point.pnl,
    }))
  }, [payoffResult])

  // Chart data for time-series payoff (multiple curves)
  const timeSeriesChartData = useMemo(() => {
    if (!timeSeriesResult) return []

    // Build combined data with all time curves
    const pricePoints = timeSeriesResult.time_curves[0]?.points || []
    return pricePoints.map((_, idx) => {
      const dataPoint: Record<string, number> = {
        price: timeSeriesResult.time_curves[0]?.points[idx]?.price || 0,
      }
      timeSeriesResult.time_curves.forEach((curve, curveIdx) => {
        dataPoint[`dte_${curve.dte}`] = curve.points[idx]?.pnl || 0
      })
      return dataPoint
    })
  }, [timeSeriesResult])

  const formatCurrency = (value: number) => {
    return value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`
  }

  const isLoading = calculatePayoff.isPending || calculateTimeSeries.isPending
  const currentResult = showTimeDecay ? timeSeriesResult : payoffResult
  const hasData = showTimeDecay ? timeSeriesChartData.length > 0 : chartData.length > 0

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Payoff Diagram</span>
          <div className="flex items-center gap-2">
            <span className="text-sm font-normal text-muted-foreground">Underlying:</span>
            <Input
              type="number"
              value={underlyingPrice}
              onChange={(e) => setUnderlyingPrice(parseFloat(e.target.value) || 0)}
              className="w-24 h-8"
            />
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Strategy Selector */}
        <div className="flex gap-2 flex-wrap">
          <Select
            value={selectedStrategy}
            onChange={(e) => applyStrategy(e.target.value)}
            className="w-48 h-8"
          >
            <option value="">Select strategy...</option>
            <option value="long_call">Long Call</option>
            <option value="long_put">Long Put</option>
            <option value="covered_call">Covered Call</option>
            <option value="bull_call_spread">Bull Call Spread</option>
            <option value="bear_put_spread">Bear Put Spread</option>
            <option value="straddle">Straddle</option>
            <option value="strangle">Strangle</option>
            <option value="iron_condor">Iron Condor</option>
            <option value="butterfly">Butterfly</option>
          </Select>
          <Button variant="outline" size="sm" onClick={addLeg}>
            <Plus className="h-3.5 w-3.5 mr-1" /> Add Leg
          </Button>
          <Button variant="outline" size="sm" onClick={() => setLegs([])}>
            Clear All
          </Button>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant={showTimeDecay ? "default" : "outline"}
              size="sm"
              onClick={() => setShowTimeDecay(!showTimeDecay)}
              className="gap-1"
            >
              <Clock className="h-3.5 w-3.5" />
              Time Decay
            </Button>
          </div>
        </div>

        {/* Time Decay Controls */}
        {showTimeDecay && (
          <div className="flex items-center gap-4 p-3 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Max DTE:</span>
              <Input
                type="number"
                value={maxDTE}
                onChange={(e) => setMaxDTE(parseInt(e.target.value) || 30)}
                className="w-20 h-8"
                min={7}
                max={365}
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">IV:</span>
              <Input
                type="number"
                value={iv}
                onChange={(e) => setIV(parseInt(e.target.value) || 30)}
                className="w-20 h-8"
                min={5}
                max={200}
              />
              <span className="text-xs text-muted-foreground">%</span>
            </div>
            <div className="text-xs text-muted-foreground ml-auto">
              Shows P/L curves at different times to expiration
            </div>
          </div>
        )}

        {/* Legs Editor */}
        {legs.length > 0 && (
          <div className="space-y-2">
            {legs.map((leg, index) => (
              <div key={index} className="flex items-center gap-2 bg-muted/50 p-2 rounded-lg">
                <Select
                  value={leg.action}
                  onChange={(e) => updateLeg(index, { action: e.target.value as ActionType })}
                  className="w-20 h-8"
                >
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </Select>
                <Select
                  value={leg.option_type}
                  onChange={(e) => updateLeg(index, { option_type: e.target.value as OptionType })}
                  className="w-20 h-8"
                >
                  <option value="call">Call</option>
                  <option value="put">Put</option>
                </Select>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">Strike:</span>
                  <Input
                    type="number"
                    value={leg.strike}
                    onChange={(e) => updateLeg(index, { strike: parseFloat(e.target.value) || 0 })}
                    className="w-20 h-8"
                  />
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">Qty:</span>
                  <Input
                    type="number"
                    value={leg.quantity}
                    onChange={(e) => updateLeg(index, { quantity: parseInt(e.target.value) || 1 })}
                    className="w-16 h-8"
                  />
                </div>
                <div className="flex items-center gap-1">
                  <span className="text-xs text-muted-foreground">Premium:</span>
                  <Input
                    type="number"
                    value={leg.premium}
                    onChange={(e) => updateLeg(index, { premium: parseFloat(e.target.value) || 0 })}
                    className="w-20 h-8"
                  />
                </div>
                <Button variant="ghost" size="icon" onClick={() => removeLeg(index)}>
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Chart */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : hasData ? (
          <>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                {showTimeDecay && timeSeriesResult ? (
                  <LineChart data={timeSeriesChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="price"
                      tickFormatter={(v) => `$${v}`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis
                      tickFormatter={(v) => `$${v}`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <Tooltip
                      formatter={(value: number, name: string) => {
                        const dte = name.replace("dte_", "")
                        const label = dte === "0" ? "Expiration" : `${dte} DTE`
                        return [formatCurrency(value), label]
                      }}
                      labelFormatter={(label) => `Price: $${label}`}
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                    />
                    <Legend
                      formatter={(value: string) => {
                        const dte = value.replace("dte_", "")
                        return dte === "0" ? "Expiration" : `${dte} DTE`
                      }}
                    />
                    <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                    <ReferenceLine x={underlyingPrice} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                    {timeSeriesResult.time_curves.map((curve, idx) => (
                      <Line
                        key={curve.dte}
                        type="monotone"
                        dataKey={`dte_${curve.dte}`}
                        stroke={TIME_CURVE_COLORS[idx % TIME_CURVE_COLORS.length]}
                        strokeWidth={curve.dte === 0 ? 2.5 : 1.5}
                        strokeDasharray={curve.dte === 0 ? undefined : "5 3"}
                        dot={false}
                        opacity={curve.dte === 0 ? 1 : 0.7}
                      />
                    ))}
                  </LineChart>
                ) : (
                  <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis
                      dataKey="price"
                      tickFormatter={(v) => `$${v}`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <YAxis
                      tickFormatter={(v) => `$${v}`}
                      tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                    />
                    <Tooltip
                      formatter={(value: number) => [formatCurrency(value), "P/L"]}
                      labelFormatter={(label) => `Price: $${label}`}
                      contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                    />
                    <ReferenceLine y={0} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                    <ReferenceLine x={underlyingPrice} stroke="hsl(var(--muted-foreground))" strokeDasharray="5 5" />
                    {payoffResult?.breakevens.map((be, i) => (
                      <ReferenceLine key={i} x={be} stroke="hsl(var(--bb-amber))" strokeDasharray="3 3" />
                    ))}
                    <Line
                      type="monotone"
                      dataKey="pnl"
                      stroke="hsl(var(--bb-blue))"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                  <TrendingUp className="h-3.5 w-3.5" />
                  Max Profit
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-green">
                  {(showTimeDecay ? timeSeriesResult?.max_profit : payoffResult?.max_profit) === null
                    ? "Unlimited"
                    : formatCurrency((showTimeDecay ? timeSeriesResult?.max_profit : payoffResult?.max_profit) || 0)}
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                  <TrendingDown className="h-3.5 w-3.5" />
                  Max Loss
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-red">
                  {(showTimeDecay ? timeSeriesResult?.max_loss : payoffResult?.max_loss) === null
                    ? "Unlimited"
                    : formatCurrency((showTimeDecay ? timeSeriesResult?.max_loss : payoffResult?.max_loss) || 0)}
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                  <DollarSign className="h-3.5 w-3.5" />
                  Net Premium
                </div>
                <span className={`text-lg font-bold tabular-nums ${((showTimeDecay ? timeSeriesResult?.net_premium : payoffResult?.net_premium) || 0) >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                  {formatCurrency((showTimeDecay ? timeSeriesResult?.net_premium : payoffResult?.net_premium) || 0)}
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                  Breakevens
                </div>
                <span className="text-lg font-bold tabular-nums text-bb-amber">
                  {((showTimeDecay ? timeSeriesResult?.expiration_breakevens : payoffResult?.breakevens) || []).length > 0
                    ? ((showTimeDecay ? timeSeriesResult?.expiration_breakevens : payoffResult?.breakevens) || [])
                        .map(be => `$${be.toFixed(2)}`).join(", ")
                    : "None"}
                </span>
              </div>
            </div>

            {/* Time Decay Legend */}
            {showTimeDecay && timeSeriesResult && (
              <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                <span className="font-medium">Time curves:</span>
                {timeSeriesResult.time_curves.map((curve, idx) => (
                  <div key={curve.dte} className="flex items-center gap-1">
                    <div
                      className="w-4 h-0.5"
                      style={{
                        backgroundColor: TIME_CURVE_COLORS[idx % TIME_CURVE_COLORS.length],
                        opacity: curve.dte === 0 ? 1 : 0.7,
                      }}
                    />
                    <span>{curve.label}</span>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <TrendingUp className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Add option legs to see the payoff diagram</p>
            <p className="text-xs text-muted-foreground mt-1">Select a strategy or add legs manually</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
