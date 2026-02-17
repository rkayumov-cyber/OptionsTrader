import { useState, useEffect, useRef } from "react"
import { Search, RefreshCw, TrendingUp, TrendingDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useStreamingQuote, useAddToWatchlist } from "@/hooks/useMarketData"
import { formatPrice, formatVolume } from "@/lib/utils"
import { PriceChart } from "@/components/PriceChart"
import type { Market } from "@/lib/api"

interface QuoteLookupProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
  initialSymbol?: string
  initialMarket?: Market
}

// Blinking price display component
function BlinkingPriceDisplay({
  price,
  currency,
  size = "lg",
}: {
  price: number | undefined
  currency: string
  size?: "lg" | "md" | "sm"
}) {
  const [flashClass, setFlashClass] = useState("")
  const [direction, setDirection] = useState<"up" | "down" | "neutral">("neutral")
  const prevPriceRef = useRef<number | null>(null)

  useEffect(() => {
    if (price === undefined) return

    const prev = prevPriceRef.current
    if (prev !== null && prev !== price) {
      const newDirection = price > prev ? "up" : price < prev ? "down" : "neutral"
      setDirection(newDirection)
      setFlashClass(newDirection === "up" ? "price-up" : newDirection === "down" ? "price-down" : "")

      const timer = setTimeout(() => setFlashClass(""), 800)
      return () => clearTimeout(timer)
    }
    prevPriceRef.current = price
  }, [price])

  const sizeClasses = {
    lg: "text-3xl",
    md: "text-xl",
    sm: "text-sm",
  }

  return (
    <span className={`font-bold price-value ${sizeClasses[size]} ${flashClass}`}>
      {direction === "up" && <span className="price-arrow up" />}
      {direction === "down" && <span className="price-arrow down" />}
      {formatPrice(price, currency)}
    </span>
  )
}

export function QuoteLookup({ onSymbolSelect, initialSymbol, initialMarket }: QuoteLookupProps) {
  const [symbol, setSymbol] = useState(initialSymbol || "")
  const [market, setMarket] = useState<Market>(initialMarket || "US")
  const [searchSymbol, setSearchSymbol] = useState(initialSymbol || "")
  const [searchMarket, setSearchMarket] = useState<Market>(initialMarket || "US")

  // Update when initial props change (e.g., from dashboard navigation)
  useEffect(() => {
    if (initialSymbol) {
      setSymbol(initialSymbol)
      setSearchSymbol(initialSymbol)
    }
    if (initialMarket) {
      setMarket(initialMarket)
      setSearchMarket(initialMarket)
    }
  }, [initialSymbol, initialMarket])

  const { data: quote, isLoading, isError, refetch, dataUpdatedAt } = useStreamingQuote(searchSymbol, searchMarket, !!searchSymbol)
  const addToWatchlist = useAddToWatchlist()

  const handleSearch = () => {
    if (symbol.trim()) {
      setSearchSymbol(symbol.trim().toUpperCase())
      setSearchMarket(market)
      onSymbolSelect?.(symbol.trim().toUpperCase(), market)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  const handleAddToWatchlist = () => {
    if (quote) {
      addToWatchlist.mutate({ symbol: quote.symbol, market: quote.market })
    }
  }

  const getCurrencyForMarket = (m: Market) => {
    const currencies: Record<Market, string> = { US: "USD", JP: "JPY", HK: "HKD" }
    return currencies[m]
  }

  const change = quote?.change ?? 0
  const changePercent = quote?.change_percent ?? 0
  const isPositive = change > 0
  const isNegative = change < 0

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          Quote Lookup
        </CardTitle>
        {quote && (
          <div className="flex items-center gap-2 text-[10px]">
            <span className="live-indicator" />
            <span className="text-muted-foreground">
              Updated {new Date(dataUpdatedAt).toLocaleTimeString("en-US", { hour12: false })}
            </span>
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex gap-2 mb-4">
          <Input
            placeholder="Enter symbol (e.g., AAPL)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            onKeyDown={handleKeyDown}
            className="flex-1"
          />
          <Select value={market} onChange={(e) => setMarket(e.target.value as Market)} className="w-20">
            <option value="US">US</option>
            <option value="JP">JP</option>
            <option value="HK">HK</option>
          </Select>
          <Button onClick={handleSearch} disabled={!symbol.trim()} size="sm">
            <Search className="h-4 w-4" />
          </Button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-4 w-4 animate-spin text-primary" />
            <span className="ml-2 text-xs text-muted-foreground">Loading...</span>
          </div>
        )}

        {isError && (
          <div className="text-center py-8 text-destructive text-xs">
            Failed to fetch quote. Please try again.
          </div>
        )}

        {quote && !isLoading && (
          <div className="space-y-4">
            {/* Main price display */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-bb-cyan">{quote.symbol}</h3>
                <p className="text-[10px] text-muted-foreground uppercase">{quote.market} Market</p>
              </div>
              <div className="text-right">
                <BlinkingPriceDisplay
                  price={quote.price}
                  currency={getCurrencyForMarket(quote.market)}
                />
                <div className={`flex items-center justify-end gap-1 text-sm mt-1 ${isPositive ? 'text-bb-green' : isNegative ? 'text-bb-red' : 'text-muted-foreground'}`}>
                  {isPositive && <TrendingUp className="h-3 w-3" />}
                  {isNegative && <TrendingDown className="h-3 w-3" />}
                  <span className="price-value">
                    {isPositive ? '+' : ''}{change.toFixed(2)}
                  </span>
                  <span className="price-value">
                    ({isPositive ? '+' : ''}{changePercent.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>

            {/* Quote details grid */}
            <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs border-t border-b border-border py-3">
              <div className="flex justify-between">
                <span className="text-muted-foreground uppercase text-[10px]">Bid</span>
                <span className="price-value text-bb-green">{formatPrice(quote.bid, getCurrencyForMarket(quote.market))}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground uppercase text-[10px]">Ask</span>
                <span className="price-value text-bb-red">{formatPrice(quote.ask, getCurrencyForMarket(quote.market))}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground uppercase text-[10px]">Volume</span>
                <span className="price-value">{formatVolume(quote.volume)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground uppercase text-[10px]">Spread</span>
                <span className="price-value text-bb-amber">
                  {quote.bid && quote.ask
                    ? formatPrice(quote.ask - quote.bid, getCurrencyForMarket(quote.market))
                    : "-"}
                </span>
              </div>
              {quote.high && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground uppercase text-[10px]">High</span>
                  <span className="price-value">{formatPrice(quote.high, getCurrencyForMarket(quote.market))}</span>
                </div>
              )}
              {quote.low && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground uppercase text-[10px]">Low</span>
                  <span className="price-value">{formatPrice(quote.low, getCurrencyForMarket(quote.market))}</span>
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-3 w-3 mr-1" />
                Refresh
              </Button>
              <Button variant="secondary" size="sm" onClick={handleAddToWatchlist}>
                Add to Watchlist
              </Button>
            </div>

            {/* Price Chart */}
            <div className="pt-4 border-t mt-4">
              <PriceChart symbol={quote.symbol} market={quote.market} />
            </div>
          </div>
        )}

        {!quote && !isLoading && !isError && searchSymbol && (
          <div className="text-center py-8 text-muted-foreground text-xs">
            No data found for {searchSymbol}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
