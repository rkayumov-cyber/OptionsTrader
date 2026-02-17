import { useState } from "react"
import { Plus, Trash2, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist, useQuote } from "@/hooks/useMarketData"
import { formatPrice } from "@/lib/utils"
import type { Market, WatchlistItem } from "@/lib/api"

interface WatchlistProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
}

function WatchlistItemRow({
  item,
  onSelect,
  onRemove,
}: {
  item: WatchlistItem
  onSelect: () => void
  onRemove: () => void
}) {
  const { data: quote, isLoading } = useQuote(item.symbol, item.market)

  const getCurrencyForMarket = (m: Market) => {
    const currencies: Record<Market, string> = { US: "USD", JP: "JPY", HK: "HKD" }
    return currencies[m]
  }

  return (
    <div
      className="flex items-center justify-between p-2 hover:bg-muted rounded-md cursor-pointer group"
      onClick={onSelect}
    >
      <div className="flex-1">
        <div className="font-medium">{item.symbol}</div>
        <div className="text-xs text-muted-foreground">{item.market}</div>
      </div>
      <div className="text-right mr-2">
        {isLoading ? (
          <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : quote ? (
          <div className="font-medium">
            {formatPrice(quote.price, getCurrencyForMarket(item.market))}
          </div>
        ) : (
          <span className="text-muted-foreground">-</span>
        )}
      </div>
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={(e) => {
          e.stopPropagation()
          onRemove()
        }}
      >
        <Trash2 className="h-4 w-4 text-destructive" />
      </Button>
    </div>
  )
}

export function Watchlist({ onSymbolSelect }: WatchlistProps) {
  const [newSymbol, setNewSymbol] = useState("")
  const [newMarket, setNewMarket] = useState<Market>("US")
  const [isAdding, setIsAdding] = useState(false)

  const { data: watchlist, isLoading } = useWatchlist()
  const addToWatchlist = useAddToWatchlist()
  const removeFromWatchlist = useRemoveFromWatchlist()

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
    if (e.key === "Enter") {
      handleAdd()
    } else if (e.key === "Escape") {
      setIsAdding(false)
      setNewSymbol("")
    }
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Watchlist</CardTitle>
          <Button variant="ghost" size="icon" onClick={() => setIsAdding(true)}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isAdding && (
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="Symbol"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              onKeyDown={handleKeyDown}
              className="flex-1"
              autoFocus
            />
            <Select
              value={newMarket}
              onChange={(e) => setNewMarket(e.target.value as Market)}
              className="w-20"
            >
              <option value="US">US</option>
              <option value="JP">JP</option>
              <option value="HK">HK</option>
            </Select>
            <Button size="sm" onClick={handleAdd} disabled={!newSymbol.trim()}>
              Add
            </Button>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-4">
            <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        )}

        {watchlist && watchlist.length === 0 && !isLoading && (
          <p className="text-sm text-muted-foreground text-center py-4">
            No symbols in watchlist
          </p>
        )}

        {watchlist && watchlist.length > 0 && (
          <div className="space-y-1">
            {watchlist.map((item) => (
              <WatchlistItemRow
                key={`${item.symbol}-${item.market}`}
                item={item}
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
