import { useState, useRef } from "react"
import { Star, Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { BlinkingPrice } from "@/components/ui/blinking-price"
import { useStreamingQuote, useIVAnalysis, useMarketSentiment, useAddToWatchlist } from "@/hooks/useMarketData"
import { formatPrice, formatVolume } from "@/lib/utils"
import type { Market } from "@/lib/api"

interface SymbolHeaderProps {
  symbol: string
  market: Market
  onSymbolChange: (symbol: string, market: Market) => void
}

const SENTIMENT_COLORS: Record<string, string> = {
  bullish: "text-bb-green",
  slightly_bullish: "text-bb-green",
  neutral: "text-bb-amber",
  slightly_bearish: "text-bb-red",
  bearish: "text-bb-red",
}

const SENTIMENT_LABELS: Record<string, string> = {
  bullish: "BULLISH",
  slightly_bullish: "SL.BULL",
  neutral: "NEUTRAL",
  slightly_bearish: "SL.BEAR",
  bearish: "BEARISH",
}

export function SymbolHeader({ symbol, market, onSymbolChange }: SymbolHeaderProps) {
  const [inputSymbol, setInputSymbol] = useState(symbol)
  const [inputMarket, setInputMarket] = useState<Market>(market)
  const inputRef = useRef<HTMLInputElement>(null)

  const { data: quote } = useStreamingQuote(symbol, market)
  const { data: iv } = useIVAnalysis(symbol, market)
  const { data: sentiment } = useMarketSentiment(symbol, market)
  const addToWatchlist = useAddToWatchlist()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = inputSymbol.trim().toUpperCase()
    if (trimmed) {
      onSymbolChange(trimmed, inputMarket)
      inputRef.current?.blur()
    }
  }

  const handleAddToWatchlist = () => {
    if (symbol) {
      addToWatchlist.mutate({ symbol, market })
    }
  }

  const getCurrency = (m: Market) => {
    const currencies: Record<Market, string> = { US: "USD", JP: "JPY", HK: "HKD" }
    return currencies[m]
  }

  const change = quote?.change ?? 0
  const changePercent = quote?.change_percent ?? 0
  const sentimentKey = sentiment?.sentiment || "neutral"

  return (
    <div className="bg-muted border border-border rounded mb-3">
      {/* Row 1: Symbol input + Price + Volume */}
      <div className="flex items-center gap-3 px-3 py-1.5 border-b border-border/50">
        {/* Left: Symbol input + market + watchlist */}
        <form onSubmit={handleSubmit} className="flex items-center gap-1.5">
          <Input
            ref={inputRef}
            value={inputSymbol}
            onChange={(e) => setInputSymbol(e.target.value.toUpperCase())}
            className="w-24 h-6 text-xs font-bold text-bb-cyan bg-secondary border-border uppercase"
            spellCheck={false}
            autoComplete="off"
          />
          <Select
            value={inputMarket}
            onChange={(e) => setInputMarket(e.target.value as Market)}
            className="w-16 h-6 text-[10px]"
          >
            <option value="US">US</option>
            <option value="JP">JP</option>
            <option value="HK">HK</option>
          </Select>
          <Button type="submit" variant="ghost" size="sm" className="h-6 w-6 p-0">
            <Search className="h-3 w-3" />
          </Button>
        </form>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleAddToWatchlist}
          className="h-6 w-6 p-0 text-bb-amber hover:text-bb-amber/80"
          title="Add to watchlist"
        >
          <Star className="h-3.5 w-3.5" />
        </Button>

        <div className="h-4 w-px bg-border" />

        {/* Center: Live price + change */}
        <div className="flex items-center gap-3">
          <BlinkingPrice
            value={quote?.price}
            format={(v) => formatPrice(v, getCurrency(market))}
            showArrow
            showChange
            changeValue={change}
            changePercent={changePercent}
            size="md"
            className="font-bold"
          />
        </div>

        <div className="h-4 w-px bg-border" />

        {/* Bid/Ask */}
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-muted-foreground">B:</span>
          <span className="text-bb-green price-value tabular-nums">{formatPrice(quote?.bid, getCurrency(market))}</span>
          <span className="text-muted-foreground">A:</span>
          <span className="text-bb-red price-value tabular-nums">{formatPrice(quote?.ask, getCurrency(market))}</span>
        </div>

        <div className="h-4 w-px bg-border" />

        {/* Volume */}
        <div className="flex items-center gap-1 text-[10px]">
          <span className="text-muted-foreground">Vol:</span>
          <span className="tabular-nums">{formatVolume(quote?.volume)}</span>
        </div>
      </div>

      {/* Row 2: IV Rank + IV Percentile + P/C Ratio + Sentiment */}
      <div className="flex items-center gap-4 px-3 py-1 text-[10px]">
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground uppercase">IV Rank:</span>
          <span className="font-semibold tabular-nums text-bb-cyan">{iv ? iv.iv_rank.toFixed(0) : "—"}</span>
        </div>
        <div className="h-3 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground uppercase">IV %ile:</span>
          <span className="font-semibold tabular-nums text-bb-cyan">{iv ? iv.iv_percentile.toFixed(0) : "—"}</span>
        </div>
        <div className="h-3 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className="text-muted-foreground uppercase">P/C:</span>
          <span className="font-semibold tabular-nums">{sentiment ? sentiment.put_call_ratio.toFixed(2) : "—"}</span>
        </div>
        <div className="h-3 w-px bg-border" />
        <div className="flex items-center gap-1.5">
          <span className={`font-bold ${SENTIMENT_COLORS[sentimentKey]}`}>
            {sentiment ? `● ${SENTIMENT_LABELS[sentimentKey]}` : "—"}
          </span>
        </div>
      </div>
    </div>
  )
}
