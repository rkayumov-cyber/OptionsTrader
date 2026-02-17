import { useState, useMemo } from "react"
import { useWatchlist, useBatchQuotes, useBatchIVAnalysis, useAddToWatchlist, useRemoveFromWatchlist } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Plus, Trash2, TrendingUp, TrendingDown, Star } from "lucide-react"
import type { Market, Quote, IVAnalysis, WatchlistItem, BatchSymbol } from "@/lib/api"

interface EnhancedWatchlistProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
  className?: string
}

interface WatchlistRowProps {
  item: WatchlistItem
  quote?: Quote
  ivData?: IVAnalysis
  isLoading: boolean
  onSelect?: () => void
  onRemove?: () => void
}

function WatchlistRow({ item, quote, ivData, isLoading, onSelect, onRemove }: WatchlistRowProps) {
  const change = quote?.change_percent || 0
  const isPositive = change >= 0

  const getIVRankColorVar = (rank: number) => {
    if (rank < 30) return "var(--bb-blue)"
    if (rank < 70) return "var(--bb-amber)"
    return "var(--bb-red)"
  }

  return (
    <div
      className="group flex items-center gap-2 p-2 hover:bg-muted/50 rounded-lg cursor-pointer transition-colors"
      onClick={onSelect}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{item.symbol}</span>
          <span className="text-xs text-muted-foreground">{item.market}</span>
        </div>
        {isLoading ? (
          <div className="text-xs text-muted-foreground">Loading...</div>
        ) : (
          <div className="flex items-center gap-1 text-xs">
            {isPositive ? (
              <TrendingUp className="h-3.5 w-3.5 text-bb-green" />
            ) : (
              <TrendingDown className="h-3.5 w-3.5 text-bb-red" />
            )}
            <span className={`tabular-nums ${isPositive ? "text-bb-green" : "text-bb-red"}`}>
              {isPositive ? "+" : ""}{change.toFixed(2)}%
            </span>
          </div>
        )}
      </div>

      {/* Price */}
      <div className="text-right w-20">
        {isLoading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
        ) : (
          <div className="font-medium text-sm tabular-nums">${quote?.price.toFixed(2)}</div>
        )}
      </div>

      {/* IV Rank */}
      <div className="text-right w-16">
        {isLoading ? (
          <span className="text-xs text-muted-foreground">--</span>
        ) : ivData ? (
          <div
            className="text-[10px] font-medium px-1.5 py-0.5 rounded-full inline-block tabular-nums"
            style={{
              backgroundColor: `hsl(${getIVRankColorVar(ivData.iv_rank)} / 0.1)`,
              color: `hsl(${getIVRankColorVar(ivData.iv_rank)})`,
            }}
          >
            {ivData.iv_rank.toFixed(0)}%
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">--</span>
        )}
      </div>

      {/* Remove button */}
      <Button
        variant="ghost"
        size="sm"
        className="h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation()
          onRemove?.()
        }}
      >
        <Trash2 className="h-3.5 w-3.5 text-destructive" />
      </Button>
    </div>
  )
}

export function EnhancedWatchlist({ onSymbolSelect, className }: EnhancedWatchlistProps) {
  const [isAdding, setIsAdding] = useState(false)
  const [newSymbol, setNewSymbol] = useState("")
  const [newMarket, setNewMarket] = useState<Market>("US")

  const { data: watchlist, isLoading } = useWatchlist()
  const addToWatchlist = useAddToWatchlist()
  const removeFromWatchlist = useRemoveFromWatchlist()

  // Build batch symbol list from watchlist
  const batchSymbols: BatchSymbol[] = useMemo(
    () => (watchlist || []).map((w) => ({ symbol: w.symbol, market: w.market })),
    [watchlist]
  )

  const { data: batchQuotes, isLoading: quotesLoading } = useBatchQuotes(batchSymbols, !!watchlist)
  const { data: batchIV, isLoading: ivLoading } = useBatchIVAnalysis(batchSymbols, !!watchlist)

  const handleAdd = () => {
    if (newSymbol.trim()) {
      addToWatchlist.mutate(
        { symbol: newSymbol.trim().toUpperCase(), market: newMarket },
        {
          onSuccess: () => {
            setNewSymbol("")
            setIsAdding(false)
          },
        }
      )
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleAdd()
    if (e.key === "Escape") {
      setIsAdding(false)
      setNewSymbol("")
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Star className="h-4 w-4 text-bb-amber" />
            Watchlist
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
            onClick={() => setIsAdding(!isAdding)}
          >
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Add form */}
        {isAdding && (
          <div className="flex gap-2 mb-3 pb-3 border-b">
            <Input
              placeholder="Symbol"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyDown={handleKeyDown}
              className="flex-1 h-8 text-sm"
              autoFocus
            />
            <Select
              value={newMarket}
              onChange={(e) => setNewMarket(e.target.value as Market)}
              className="w-20 h-8 text-sm"
            >
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="HK">HK</option>
            </Select>
            <Button size="sm" className="h-8" onClick={handleAdd} disabled={!newSymbol.trim()}>
              Add
            </Button>
          </div>
        )}

        {/* Column headers */}
        <div className="flex items-center gap-2 px-2 pb-2 border-b text-xs text-muted-foreground">
          <div className="flex-1">Symbol</div>
          <div className="w-20 text-right">Price</div>
          <div className="w-16 text-right">IV Rank</div>
          <div className="w-7"></div>
        </div>

        {/* Watchlist items */}
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : !watchlist || watchlist.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
            <Star className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No symbols in watchlist</p>
            <Button
              variant="link"
              size="sm"
              onClick={() => setIsAdding(true)}
              className="mt-1"
            >
              Add your first symbol
            </Button>
          </div>
        ) : (
          <div className="space-y-1 mt-2 max-h-[480px] overflow-y-auto">
            {watchlist.map((item) => (
              <WatchlistRow
                key={`${item.symbol}-${item.market}`}
                item={item}
                quote={batchQuotes?.[item.symbol] as Quote | undefined}
                ivData={batchIV?.[item.symbol] as IVAnalysis | undefined}
                isLoading={quotesLoading || ivLoading}
                onSelect={() => onSymbolSelect?.(item.symbol, item.market)}
                onRemove={() =>
                  removeFromWatchlist.mutate({ symbol: item.symbol, market: item.market })
                }
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
