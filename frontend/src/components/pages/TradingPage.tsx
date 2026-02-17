import { useState, useEffect } from "react"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { PositionTracker } from "@/components/PositionTracker"
import { PaperTrading } from "@/components/PaperTrading"
import { TradeJournal } from "@/components/TradeJournal"
import { AlertsManager } from "@/components/AlertsManager"

interface TradingPageProps {
  defaultTab?: string
}

export function TradingPage({ defaultTab }: TradingPageProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || "positions")

  useEffect(() => {
    if (defaultTab) setActiveTab(defaultTab)
  }, [defaultTab])

  const TAB_HINTS: Record<string, string> = {
    positions: "Track open and closed option positions with multi-leg support and aggregated Greeks. Create positions to monitor P&L and run health checks in the Engine tab.",
    paper: "Practice trading with a virtual $100K account. Place market and limit orders for stocks and options without risking real capital.",
    journal: "Log every trade with entry/exit prices, strategy tags, and lessons learned. Review your win rate, average P&L, and profit factor over time.",
    alerts: "Set price, IV, and volume alerts on any symbol. Notifications appear here when thresholds are breached.",
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList className="h-8 bg-muted/50 border border-border">
        <TabsTrigger value="positions" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Positions
        </TabsTrigger>
        <TabsTrigger value="paper" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Paper Trade
        </TabsTrigger>
        <TabsTrigger value="journal" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Journal
        </TabsTrigger>
        <TabsTrigger value="alerts" className="text-xs px-3 py-1 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
          Alerts
        </TabsTrigger>
      </TabsList>
      {TAB_HINTS[activeTab] && (
        <p className="text-muted-foreground text-[10px] mt-1 mb-0 px-1">{TAB_HINTS[activeTab]}</p>
      )}

      <TabsContent value="positions">
        <PositionTracker />
      </TabsContent>

      <TabsContent value="paper">
        <PaperTrading />
      </TabsContent>

      <TabsContent value="journal">
        <TradeJournal />
      </TabsContent>

      <TabsContent value="alerts">
        <AlertsManager />
      </TabsContent>
    </Tabs>
  )
}
