import { useState, useMemo } from "react"
import { useBatchQuotes } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TrendingUp, TrendingDown, Loader2 } from "lucide-react"
import type { Market, Quote, BatchSymbol } from "@/lib/api"

interface MarketMoversProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
  className?: string
}

type TabType = "gainers" | "losers" | "active"

// Index symbols to track
const TRACKED_SYMBOLS: Array<{ symbol: string; market: Market; name: string }> = [
  { symbol: "SPY", market: "US", name: "S&P 500" },
  { symbol: "QQQ", market: "US", name: "Nasdaq 100" },
  { symbol: "AAPL", market: "US", name: "Apple" },
  { symbol: "MSFT", market: "US", name: "Microsoft" },
  { symbol: "GOOGL", market: "US", name: "Alphabet" },
  { symbol: "NVDA", market: "US", name: "NVIDIA" },
  { symbol: "NKY", market: "JP", name: "Nikkei 225" },
  { symbol: "HSI", market: "HK", name: "Hang Seng" },
]

const BATCH_SYMBOLS: BatchSymbol[] = TRACKED_SYMBOLS.map((s) => ({
  symbol: s.symbol,
  market: s.market,
}))

function MoverRow({
  quote,
  name,
  onClick,
}: {
  quote: Quote
  name: string
  onClick?: () => void
}) {
  const change = quote.change_percent || 0
  const isPositive = change >= 0

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center justify-between py-2 px-2 hover:bg-muted/50 rounded-lg transition-colors"
    >
      <div className="flex items-center gap-2">
        {isPositive ? (
          <TrendingUp className="h-3.5 w-3.5 text-bb-green" />
        ) : (
          <TrendingDown className="h-3.5 w-3.5 text-bb-red" />
        )}
        <div className="text-left">
          <div className="font-medium text-sm">{quote.symbol}</div>
          <div className="text-xs text-muted-foreground">{name}</div>
        </div>
      </div>
      <div className="text-right">
        <div className="text-sm font-medium tabular-nums">${quote.price.toFixed(2)}</div>
        <div
          className={`text-xs font-medium tabular-nums ${isPositive ? "text-bb-green" : "text-bb-red"}`}
        >
          {isPositive ? "+" : ""}
          {change.toFixed(2)}%
        </div>
      </div>
    </button>
  )
}

export function MarketMovers({ onSymbolSelect, className }: MarketMoversProps) {
  const [activeTab, setActiveTab] = useState<TabType>("gainers")

  // Fetch all quotes in a single batch request
  const { data: batchQuotes, isLoading } = useBatchQuotes(BATCH_SYMBOLS)

  // Process and sort quotes based on active tab
  const sortedItems = useMemo(() => {
    if (!batchQuotes) return []

    const validItems = TRACKED_SYMBOLS
      .map((item) => {
        const quote = batchQuotes[item.symbol] as Quote | undefined
        return quote && !("error" in quote) ? { quote, name: item.name, market: item.market } : null
      })
      .filter((x): x is NonNullable<typeof x> => x !== null)

    switch (activeTab) {
      case "gainers":
        return validItems
          .filter((q) => (q.quote.change_percent || 0) > 0)
          .sort((a, b) => (b.quote.change_percent || 0) - (a.quote.change_percent || 0))
          .slice(0, 5)
      case "losers":
        return validItems
          .filter((q) => (q.quote.change_percent || 0) < 0)
          .sort((a, b) => (a.quote.change_percent || 0) - (b.quote.change_percent || 0))
          .slice(0, 5)
      case "active":
        return validItems
          .sort((a, b) => (b.quote.volume || 0) - (a.quote.volume || 0))
          .slice(0, 5)
      default:
        return validItems
    }
  }, [batchQuotes, activeTab])

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg">Market Movers</CardTitle>
        <div className="flex gap-1 mt-2">
          {(["gainers", "losers", "active"] as TabType[]).map((tab) => (
            <Button
              key={tab}
              size="sm"
              variant={activeTab === tab ? "default" : "outline"}
              onClick={() => setActiveTab(tab)}
              className="h-7 text-xs capitalize"
            >
              {tab === "active" ? "Most Active" : `Top ${tab}`}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : sortedItems.length === 0 ? (
          <div className="flex items-center justify-center h-40 text-muted-foreground text-sm">
            No {activeTab} found
          </div>
        ) : (
          <div className="space-y-1">
            {sortedItems.map((item) => (
              <MoverRow
                key={item.quote.symbol}
                quote={item.quote}
                name={item.name}
                onClick={() => onSymbolSelect?.(item.quote.symbol, item.market)}
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
