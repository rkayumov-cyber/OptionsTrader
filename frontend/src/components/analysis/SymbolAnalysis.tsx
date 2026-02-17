import { useState, useEffect } from "react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { SymbolHeader } from "./SymbolHeader"
import { SymbolOverview } from "./SymbolOverview"
import { OptionsChain } from "@/components/OptionsChain"
import { VolatilitySurface } from "@/components/VolatilitySurface"
import { VolatilitySurface3D } from "@/components/VolatilitySurface3D"
import { TermStructure } from "@/components/analytics/TermStructure"
import { SkewChart } from "@/components/analytics/SkewChart"
import { PayoffDiagram } from "@/components/PayoffDiagram"
import { ProbabilityCalculator } from "@/components/analytics/ProbabilityCalculator"
import { JPMResearchDashboard } from "@/components/jpm"
import { EarningsCalendar } from "@/components/risk/EarningsCalendar"
import { IVChart } from "@/components/analytics/IVChart"
import type { Market } from "@/lib/api"

interface SymbolAnalysisProps {
  symbol: string
  market: Market
  onSymbolChange: (symbol: string, market: Market) => void
  defaultTab?: string
}

export function SymbolAnalysis({ symbol, market, onSymbolChange, defaultTab }: SymbolAnalysisProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || "overview")

  useEffect(() => {
    if (defaultTab) setActiveTab(defaultTab)
  }, [defaultTab])

  return (
    <div>
      {/* Persistent header - always visible */}
      <SymbolHeader symbol={symbol} market={market} onSymbolChange={onSymbolChange} />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="h-8 bg-muted/50 border border-border">
          <TabsTrigger value="overview" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Overview
          </TabsTrigger>
          <TabsTrigger value="options" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Options
          </TabsTrigger>
          <TabsTrigger value="volatility" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Volatility
          </TabsTrigger>
          <TabsTrigger value="strategy" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Strategy
          </TabsTrigger>
          <TabsTrigger value="research" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Research
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Overview */}
        <TabsContent value="overview">
          <SymbolOverview symbol={symbol} market={market} />
        </TabsContent>

        {/* Tab 2: Options */}
        <TabsContent value="options">
          <OptionsChain symbol={symbol} market={market} />
        </TabsContent>

        {/* Tab 3: Volatility */}
        <TabsContent value="volatility">
          <div className="space-y-3">
            {/* Top row: Term Structure + Skew */}
            <div className="grid grid-cols-2 gap-3">
              <TermStructure symbol={symbol} market={market} />
              <SkewChart symbol={symbol} market={market} />
            </div>
            {/* Bottom row: Vol Surface 2D + 3D */}
            <div className="grid grid-cols-2 gap-3">
              <VolatilitySurface symbol={symbol} market={market} />
              <VolatilitySurface3D initialSymbol={symbol} initialMarket={market} />
            </div>
          </div>
        </TabsContent>

        {/* Tab 4: Strategy */}
        <TabsContent value="strategy">
          <div className="grid grid-cols-5 gap-3">
            <div className="col-span-3">
              <PayoffDiagram initialPrice={150} />
            </div>
            <div className="col-span-2">
              <ProbabilityCalculator symbol={symbol} market={market} />
            </div>
          </div>
        </TabsContent>

        {/* Tab 5: Research */}
        <TabsContent value="research">
          <div className="space-y-3">
            <JPMResearchDashboard />
            <EarningsCalendar />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
