import { useState, useMemo } from "react"
import {
  AreaChart,
  Area,
  ComposedChart,
  BarChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts"
import { usePriceHistory } from "@/hooks/useMarketData"
import { formatPrice } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Loader2, TrendingUp, CandlestickChart } from "lucide-react"
import type { Market } from "@/lib/api"

// Moving average periods and colors
const MA_CONFIG = [
  { period: 20, color: "hsl(var(--bb-amber))", label: "MA20" },
  { period: 50, color: "hsl(var(--bb-blue))", label: "MA50" },
  { period: 200, color: "hsl(var(--bb-cyan))", label: "MA200" },
] as const

// Calculate Simple Moving Average
function calculateSMA(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / period)
    }
  }
  return result
}

interface PriceChartProps {
  symbol: string
  market: Market
}

type ChartType = "area" | "candlestick"

const INTERVALS = [
  { label: "1D", value: "5m", limit: 78 },
  { label: "1W", value: "1h", limit: 40 },
  { label: "1M", value: "1d", limit: 22 },
  { label: "3M", value: "1d", limit: 66 },
  { label: "1Y", value: "1d", limit: 252 },
]

interface CandlestickData {
  time: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  isUp: boolean
  ma20?: number | null
  ma50?: number | null
  ma200?: number | null
}

// Custom Candlestick shape for Recharts
const CandlestickShape = (props: any) => {
  const { x, y, width, height, payload } = props
  if (!payload) return null

  const { open, close, high, low, isUp } = payload
  const color = isUp ? "hsl(var(--bb-green))" : "hsl(var(--bb-red))"

  // Calculate positions based on the actual y-axis scale
  const yScale = props.yAxis?.scale
  if (!yScale) return null

  const openY = yScale(open)
  const closeY = yScale(close)
  const highY = yScale(high)
  const lowY = yScale(low)

  const candleX = x + width / 2
  const bodyWidth = Math.max(width * 0.6, 4)
  const wickWidth = 1

  const bodyTop = Math.min(openY, closeY)
  const bodyHeight = Math.abs(closeY - openY) || 1

  return (
    <g>
      {/* Upper wick */}
      <line
        x1={candleX}
        y1={highY}
        x2={candleX}
        y2={bodyTop}
        stroke={color}
        strokeWidth={wickWidth}
      />
      {/* Lower wick */}
      <line
        x1={candleX}
        y1={Math.max(openY, closeY)}
        x2={candleX}
        y2={lowY}
        stroke={color}
        strokeWidth={wickWidth}
      />
      {/* Body */}
      <rect
        x={candleX - bodyWidth / 2}
        y={bodyTop}
        width={bodyWidth}
        height={bodyHeight}
        fill={isUp ? color : color}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  )
}

// Custom tooltip for candlestick
const CandlestickTooltip = ({ active, payload, label, currency }: any) => {
  if (!active || !payload || !payload[0]) return null

  const data = payload[0].payload
  return (
    <div className="bg-card border border-border rounded-lg p-2 text-xs">
      <div className="text-muted-foreground mb-1">{label}</div>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span className="text-muted-foreground">Open:</span>
        <span>{formatPrice(data.open, currency)}</span>
        <span className="text-muted-foreground">High:</span>
        <span className="text-bb-green">{formatPrice(data.high, currency)}</span>
        <span className="text-muted-foreground">Low:</span>
        <span className="text-bb-red">{formatPrice(data.low, currency)}</span>
        <span className="text-muted-foreground">Close:</span>
        <span className={data.isUp ? "text-bb-green" : "text-bb-red"}>
          {formatPrice(data.close, currency)}
        </span>
        <span className="text-muted-foreground">Volume:</span>
        <span>{formatVolume(data.volume)}</span>
      </div>
    </div>
  )
}

// Custom tooltip for volume bars
const VolumeTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload[0]) return null

  const data = payload[0].payload
  return (
    <div className="bg-card border border-border rounded-lg p-2 text-xs">
      <div className="text-muted-foreground mb-1">{label}</div>
      <div className="flex gap-2">
        <span className="text-muted-foreground">Volume:</span>
        <span>{formatVolume(data.volume)}</span>
      </div>
    </div>
  )
}

// Format volume with K/M/B suffix
function formatVolume(volume: number): string {
  if (volume >= 1_000_000_000) {
    return (volume / 1_000_000_000).toFixed(2) + "B"
  }
  if (volume >= 1_000_000) {
    return (volume / 1_000_000).toFixed(2) + "M"
  }
  if (volume >= 1_000) {
    return (volume / 1_000).toFixed(2) + "K"
  }
  return volume.toString()
}

export function PriceChart({ symbol, market }: PriceChartProps) {
  const [selectedInterval, setSelectedInterval] = useState(INTERVALS[2])
  const [chartType, setChartType] = useState<ChartType>("area")
  const [visibleMAs, setVisibleMAs] = useState<Set<number>>(new Set([20])) // MA20 visible by default

  const { data: history, isLoading } = usePriceHistory(
    symbol,
    market,
    selectedInterval.value,
    selectedInterval.limit
  )

  // Calculate moving averages - must be called unconditionally (React hooks rules)
  const closePrices = useMemo(() => history?.bars?.map((bar) => bar.close) ?? [], [history?.bars])
  const ma20Values = useMemo(() => calculateSMA(closePrices, 20), [closePrices])
  const ma50Values = useMemo(() => calculateSMA(closePrices, 50), [closePrices])
  const ma200Values = useMemo(() => calculateSMA(closePrices, 200), [closePrices])

  const toggleMA = (period: number) => {
    setVisibleMAs((prev) => {
      const next = new Set(prev)
      if (next.has(period)) {
        next.delete(period)
      } else {
        next.add(period)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!history || history.bars.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        No price data available
      </div>
    )
  }

  const chartData: CandlestickData[] = history.bars.map((bar, index) => ({
    time: formatTime(bar.timestamp, selectedInterval.value),
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
    volume: bar.volume,
    isUp: bar.close >= bar.open,
    ma20: ma20Values[index],
    ma50: ma50Values[index],
    ma200: ma200Values[index],
  }))

  const allPrices = chartData.flatMap((d) => [d.high, d.low])
  const minPrice = Math.min(...allPrices)
  const maxPrice = Math.max(...allPrices)
  const priceRange = maxPrice - minPrice
  const yDomain = [
    Math.floor((minPrice - priceRange * 0.05) * 100) / 100,
    Math.ceil((maxPrice + priceRange * 0.05) * 100) / 100,
  ]

  const firstPrice = chartData[0]?.close || 0
  const lastPrice = chartData[chartData.length - 1]?.close || 0
  const priceChange = lastPrice - firstPrice
  const percentChange = firstPrice > 0 ? (priceChange / firstPrice) * 100 : 0
  const isPositive = priceChange >= 0

  const getCurrency = (m: Market) => {
    const currencies: Record<Market, string> = { US: "USD", JP: "JPY", HK: "HKD" }
    return currencies[m]
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {/* Interval buttons */}
          <div className="flex gap-1">
            {INTERVALS.map((interval) => (
              <Button
                key={interval.label}
                size="sm"
                variant={selectedInterval.label === interval.label ? "default" : "outline"}
                onClick={() => setSelectedInterval(interval)}
                className="px-3 h-7 text-xs"
              >
                {interval.label}
              </Button>
            ))}
          </div>

          {/* Chart type toggle */}
          <div className="flex gap-1 ml-2 border-l pl-2">
            <Button
              size="sm"
              variant={chartType === "area" ? "default" : "outline"}
              onClick={() => setChartType("area")}
              className="h-7 px-2"
              title="Area Chart"
            >
              <TrendingUp className="h-3.5 w-3.5" />
            </Button>
            <Button
              size="sm"
              variant={chartType === "candlestick" ? "default" : "outline"}
              onClick={() => setChartType("candlestick")}
              className="h-7 px-2"
              title="Candlestick Chart"
            >
              <CandlestickChart className="h-3.5 w-3.5" />
            </Button>
          </div>

          {/* Moving average toggles */}
          <div className="flex gap-1 ml-2 border-l pl-2">
            {MA_CONFIG.map((ma) => (
              <Button
                key={ma.period}
                size="sm"
                variant={visibleMAs.has(ma.period) ? "default" : "outline"}
                onClick={() => toggleMA(ma.period)}
                className="h-7 px-2 text-xs"
                style={{
                  backgroundColor: visibleMAs.has(ma.period) ? ma.color : undefined,
                  borderColor: ma.color,
                  color: visibleMAs.has(ma.period) ? "#fff" : ma.color,
                }}
                title={`${ma.period}-period Moving Average`}
              >
                {ma.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="text-right">
          <span
            className={`text-sm font-medium ${
              isPositive ? "text-bb-green" : "text-bb-red"
            }`}
          >
            {isPositive ? "+" : ""}
            {formatPrice(priceChange, getCurrency(market))} ({isPositive ? "+" : ""}
            {percentChange.toFixed(2)}%)
          </span>
        </div>
      </div>

      {/* Price Chart */}
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "area" ? (
            <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="5%"
                    stopColor={isPositive ? "hsl(var(--bb-green))" : "hsl(var(--bb-red))"}
                    stopOpacity={0.3}
                  />
                  <stop
                    offset="95%"
                    stopColor={isPositive ? "hsl(var(--bb-green))" : "hsl(var(--bb-red))"}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                hide={true}
              />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toFixed(2)}
                width={60}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                }}
                labelStyle={{ color: "hsl(var(--muted-foreground))" }}
                formatter={(value: number) => [
                  formatPrice(value, getCurrency(market)),
                  "Price",
                ]}
              />
              <ReferenceLine
                y={firstPrice}
                stroke="hsl(var(--muted-foreground))"
                strokeDasharray="3 3"
                strokeWidth={1}
              />
              <Area
                type="monotone"
                dataKey="close"
                stroke={isPositive ? "hsl(var(--bb-green))" : "hsl(var(--bb-red))"}
                strokeWidth={2}
                fill="url(#priceGradient)"
              />
              {visibleMAs.has(20) && (
                <Line
                  type="monotone"
                  dataKey="ma20"
                  stroke="hsl(var(--bb-amber))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
              {visibleMAs.has(50) && (
                <Line
                  type="monotone"
                  dataKey="ma50"
                  stroke="hsl(var(--bb-blue))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
              {visibleMAs.has(200) && (
                <Line
                  type="monotone"
                  dataKey="ma200"
                  stroke="hsl(var(--bb-cyan))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
            </AreaChart>
          ) : (
            <ComposedChart data={chartData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                hide={true}
              />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toFixed(2)}
                width={60}
              />
              <Tooltip content={<CandlestickTooltip currency={getCurrency(market)} />} />
              <ReferenceLine
                y={firstPrice}
                stroke="hsl(var(--muted-foreground))"
                strokeDasharray="3 3"
                strokeWidth={1}
              />
              <Bar dataKey="high" shape={<CandlestickShape />} />
              {visibleMAs.has(20) && (
                <Line
                  type="monotone"
                  dataKey="ma20"
                  stroke="hsl(var(--bb-amber))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
              {visibleMAs.has(50) && (
                <Line
                  type="monotone"
                  dataKey="ma50"
                  stroke="hsl(var(--bb-blue))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
              {visibleMAs.has(200) && (
                <Line
                  type="monotone"
                  dataKey="ma200"
                  stroke="hsl(var(--bb-cyan))"
                  strokeWidth={1.5}
                  dot={false}
                  connectNulls={false}
                />
              )}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      <div className="h-16">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 0, right: 5, left: 0, bottom: 5 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fontSize: 9, fill: "hsl(var(--muted-foreground))" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatVolume(value)}
              width={60}
            />
            <Tooltip content={<VolumeTooltip />} />
            <Bar dataKey="volume" radius={[2, 2, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.isUp ? "hsla(var(--bb-green), 0.6)" : "hsla(var(--bb-red), 0.6)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function formatTime(timestamp: string, interval: string): string {
  const date = new Date(timestamp)

  if (interval === "5m" || interval === "1h") {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }

  return date.toLocaleDateString([], { month: "short", day: "numeric" })
}
