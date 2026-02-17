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
