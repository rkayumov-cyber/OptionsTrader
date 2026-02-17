import { useState, useEffect } from "react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { OptionsScanner } from "@/components/OptionsScanner"
import { EarningsCalendar } from "@/components/risk/EarningsCalendar"
import { CorrelationMatrix } from "@/components/risk/CorrelationMatrix"
import { StressTester } from "@/components/risk/StressTester"
import type { Market } from "@/lib/api"

interface RiskPageProps {
  defaultTab?: string
  onSelectSymbol?: (symbol: string, market: Market) => void
}

export function RiskPage({ defaultTab, onSelectSymbol }: RiskPageProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || "scanner")

  useEffect(() => {
    if (defaultTab) setActiveTab(defaultTab)
  }, [defaultTab])

  const TAB_HINTS: Record<string, string> = {
    scanner: "Find options opportunities: high IV stocks for premium selling, low IV for buying, and unusual volume spikes that may signal institutional activity.",
    earnings: "Upcoming earnings dates with estimated EPS, pre-earnings IV levels, and expected post-earnings IV crush. Plan event trades around these dates.",
    correlation: "Pairwise correlation matrix for any symbol group. Identify diversification opportunities or spot concentration risk in your portfolio.",
    stress: "Simulate market scenarios (crash, rally, vol spike) against your open positions. See the P&L impact before it happens.",
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList className="h-8 bg-muted/50 border border-border">
        <TabsTrigger value="scanner" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Scanner
        </TabsTrigger>
        <TabsTrigger value="earnings" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Earnings
        </TabsTrigger>
        <TabsTrigger value="correlation" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Correlation
        </TabsTrigger>
        <TabsTrigger value="stress" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Stress Test
        </TabsTrigger>
      </TabsList>
      {TAB_HINTS[activeTab] && (
        <p className="text-muted-foreground text-[10px] mt-1 mb-0 px-1">{TAB_HINTS[activeTab]}</p>
      )}

      <TabsContent value="scanner">
        <OptionsScanner onSelectSymbol={onSelectSymbol} />
      </TabsContent>

      <TabsContent value="earnings">
        <EarningsCalendar />
      </TabsContent>

      <TabsContent value="correlation">
        <CorrelationMatrix />
      </TabsContent>

      <TabsContent value="stress">
        <StressTester />
      </TabsContent>
    </Tabs>
  )
}
