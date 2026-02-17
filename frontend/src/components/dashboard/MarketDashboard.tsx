import { useState } from "react"
import { VIXGauge } from "./VIXGauge"
import { FearGreedGauge } from "./FearGreedGauge"
import { PutCallRatio } from "./PutCallRatio"
import { MarketMovers } from "./MarketMovers"
import { GreeksSummary } from "./GreeksSummary"
import { UnusualActivity } from "./UnusualActivity"
import { StrategySuggestions } from "./StrategySuggestions"
import { EnhancedWatchlist } from "./EnhancedWatchlist"
import { BondRatesPanel } from "./BondRatesPanel"
import { CommoditiesPanel } from "./CommoditiesPanel"
import { SectorHeatmap } from "./SectorHeatmap"
import { MarketBreadthPanel } from "./MarketBreadthPanel"
import type { Market } from "@/lib/api"

interface MarketDashboardProps {
  onSymbolSelect?: (symbol: string, market: Market) => void
  selectedSymbol?: string
  selectedMarket?: Market
}

export function MarketDashboard({
  onSymbolSelect,
  selectedSymbol = "SPY",
  selectedMarket = "US",
}: MarketDashboardProps) {
  const [focusedSymbol, setFocusedSymbol] = useState(selectedSymbol)
  const [focusedMarket, setFocusedMarket] = useState<Market>(selectedMarket)

  const handleSymbolSelect = (symbol: string, market: Market) => {
    setFocusedSymbol(symbol)
    setFocusedMarket(market)
    onSymbolSelect?.(symbol, market)
  }

  return (
    <div className="space-y-2">
      {/* Quick Start Guide */}
      <div className="bg-zinc-900/50 border border-zinc-700/50 rounded px-3 py-2 flex items-center gap-4 text-[10px] text-zinc-500">
        <span className="text-blue-400 font-medium uppercase tracking-wider shrink-0">Quick Start</span>
        <span>
          Press <kbd className="bb-kbd text-[9px]">/</kbd> to open the command bar and type a symbol (e.g., AAPL) to analyze it.
          Use <kbd className="bb-kbd text-[9px]">F5</kbd> for the decision engine.
          Click any symbol below to focus it. Switch data providers in the top-right header dropdown.
        </span>
      </div>

      {/* Top Row: VIX, Fear/Greed, P/C Ratio, Market Movers */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
        <VIXGauge className="h-full" />
        <FearGreedGauge className="h-full" />
        <PutCallRatio
          symbol={focusedSymbol}
          market={focusedMarket}
          className="h-full"
        />
        <MarketMovers
          onSymbolSelect={handleSymbolSelect}
          className="md:col-span-2 lg:col-span-1"
        />
      </div>

      {/* Market Indicators Row: Bonds, Commodities, Breadth, Sectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
        <BondRatesPanel className="h-full" />
        <CommoditiesPanel className="h-full" />
        <MarketBreadthPanel className="h-full" />
        <SectorHeatmap
          onSectorSelect={handleSymbolSelect}
          className="h-full"
        />
      </div>

      {/* Middle Row: Watchlist and Unusual Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        <EnhancedWatchlist
          onSymbolSelect={handleSymbolSelect}
          className="lg:col-span-2"
        />
        <UnusualActivity
          onSymbolSelect={handleSymbolSelect}
          className="h-full"
        />
      </div>

      {/* Greeks Summary Row */}
      <GreeksSummary symbol={focusedSymbol} market={focusedMarket} />

      {/* Strategy Suggestions Row */}
      <StrategySuggestions symbol={focusedSymbol} market={focusedMarket} />

      {/* Selected Symbol Indicator */}
      {focusedSymbol && (
        <div className="text-center text-[10px] text-muted-foreground py-1 border-t border-border">
          <span className="text-primary uppercase tracking-wider">Focus:</span>{" "}
          <span className="font-semibold text-bb-cyan">{focusedSymbol}</span>
          <span className="text-muted-foreground ml-1">({focusedMarket})</span>
          <span className="mx-2 text-border">|</span>
          <span>Click any symbol to update analysis</span>
        </div>
      )}
    </div>
  )
}
