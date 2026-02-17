import { useState, useEffect, useRef } from "react"
import { TrendingUp, TrendingDown } from "lucide-react"
import { useStreamingQuote } from "@/hooks/useMarketData"
import { formatPrice } from "@/lib/utils"
import type { Market } from "@/lib/api"

interface IndexItemProps {
  symbol: string
  name: string
  market: Market
}

const INDEXES: IndexItemProps[] = [
  // US Markets
  { symbol: "SPY", name: "SPX", market: "US" },
  { symbol: "QQQ", name: "NDX", market: "US" },
  { symbol: "DIA", name: "DJI", market: "US" },
  { symbol: "IWM", name: "RUT", market: "US" },
  { symbol: "VIX", name: "VIX", market: "US" },
  // Bonds / Rates
  { symbol: "^TNX", name: "10Y", market: "US" },
  // Commodities
  { symbol: "GLD", name: "GOLD", market: "US" },
  { symbol: "USO", name: "OIL", market: "US" },
  // Japan
  { symbol: "NKY", name: "NKY", market: "JP" },
  // Hong Kong
  { symbol: "HSI", name: "HSI", market: "HK" },
]

function IndexItem({ symbol, name, market }: IndexItemProps) {
  const { data: quote, isLoading, dataUpdatedAt } = useStreamingQuote(symbol, market)
  const [flashClass, setFlashClass] = useState<string>("")
  const [priceDirection, setPriceDirection] = useState<"up" | "down" | "neutral">("neutral")
  const prevPriceRef = useRef<number | null>(null)
  const prevUpdateRef = useRef<number>(0)

  // Detect price changes and trigger flash animation
  useEffect(() => {
    if (!quote?.price) return

    const currentPrice = quote.price
    const prevPrice = prevPriceRef.current

    // Only flash if this is a new update (not initial load) and price changed
    if (prevPrice !== null && prevPrice !== currentPrice && dataUpdatedAt !== prevUpdateRef.current) {
      const direction = currentPrice > prevPrice ? "up" : currentPrice < prevPrice ? "down" : "neutral"
      setPriceDirection(direction)
      setFlashClass(direction === "up" ? "price-up" : direction === "down" ? "price-down" : "")

      // Clear flash after animation
      const timer = setTimeout(() => {
        setFlashClass("")
      }, 800)

      return () => clearTimeout(timer)
    }

    prevPriceRef.current = currentPrice
    prevUpdateRef.current = dataUpdatedAt
  }, [quote?.price, dataUpdatedAt])

  if (isLoading) {
    return (
      <div className="bb-ticker-item">
        <span className="bb-ticker-symbol">{name}</span>
        <span className="text-muted-foreground bb-loading">---</span>
      </div>
    )
  }

  if (!quote) {
    return null
  }

  const change = quote.change ?? 0
  const changePercent = quote.change_percent ?? 0
  const isPositive = change > 0
  const isNegative = change < 0

  return (
    <div className="bb-ticker-item">
      <span className="bb-ticker-symbol">{name}</span>
      <span className={`bb-ticker-price price-value ${flashClass}`}>
        {priceDirection === "up" && <span className="price-arrow up" />}
        {priceDirection === "down" && <span className="price-arrow down" />}
        {formatPrice(quote.price)}
      </span>
      <span className={`flex items-center gap-0.5 ${isPositive ? 'bb-ticker-change up' : isNegative ? 'bb-ticker-change down' : 'text-muted-foreground'}`}>
        {isPositive && <TrendingUp className="h-3 w-3" />}
        {isNegative && <TrendingDown className="h-3 w-3" />}
        <span className="price-value">{isPositive ? '+' : ''}{changePercent.toFixed(2)}%</span>
      </span>
    </div>
  )
}

function LiveClock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <span className="text-muted-foreground text-xs tabular-nums">
      {time.toLocaleTimeString("en-US", { hour12: false })}
    </span>
  )
}

export function IndexTicker() {
  return (
    <div className="bb-ticker">
      <div className="flex items-center justify-start overflow-x-auto">
        {INDEXES.map((index) => (
          <IndexItem key={index.symbol} {...index} />
        ))}
        <div className="bb-ticker-item border-l border-border ml-2 pl-4 flex items-center gap-2">
          <span className="live-indicator" />
          <span className="text-[10px] text-muted-foreground uppercase">Live</span>
          <LiveClock />
        </div>
      </div>
    </div>
  )
}
