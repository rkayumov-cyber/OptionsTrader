import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Loader2, Search, TrendingUp, TrendingDown, Activity, Zap } from "lucide-react"
import {
  useHighIVOpportunities,
  useLowIVOpportunities,
  useHighVolumeActivity,
  useScanOptions,
} from "@/hooks/useMarketData"
import type { Market, ScanResult, ScanCriteria } from "@/lib/api"

interface OptionsScannerProps {
  onSelectSymbol?: (symbol: string, market: Market) => void
  className?: string
}

const SENTIMENT_COLORS: Record<string, string> = {
  bullish: "text-bb-green",
  slightly_bullish: "text-bb-green",
  neutral: "text-bb-muted",
  slightly_bearish: "text-bb-red",
  bearish: "text-bb-red",
}

const SENTIMENT_LABELS: Record<string, string> = {
  bullish: "Bullish",
  slightly_bullish: "Slightly Bullish",
  neutral: "Neutral",
  slightly_bearish: "Slightly Bearish",
  bearish: "Bearish",
}

export function OptionsScanner({ onSelectSymbol, className }: OptionsScannerProps) {
  const [market, setMarket] = useState<Market>("US")
  const [activeTab, setActiveTab] = useState("high-iv")
  const [customCriteria, setCustomCriteria] = useState<ScanCriteria>({
    market: "US",
    iv_rank_min: undefined,
    iv_rank_max: undefined,
    volume_min: undefined,
    price_min: undefined,
    price_max: undefined,
  })

  const { data: highIVData, isLoading: highIVLoading } = useHighIVOpportunities(market)
  const { data: lowIVData, isLoading: lowIVLoading } = useLowIVOpportunities(market)
  const { data: highVolumeData, isLoading: highVolumeLoading } = useHighVolumeActivity(market)
  const customScan = useScanOptions()

  const handleCustomScan = () => {
    customScan.mutate({ ...customCriteria, market })
  }

  const renderResults = (results: ScanResult[] | undefined, isLoading: boolean) => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )
    }

    if (!results || results.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
          <Search className="h-8 w-8 mb-2 opacity-50" />
          <p className="text-sm">No results found</p>
        </div>
      )
    }

    return (
      <div className="space-y-2 max-h-[480px] overflow-y-auto">
        {results.map((result, index) => (
          <div
            key={`${result.symbol}-${index}`}
            className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 cursor-pointer transition-colors"
            onClick={() => onSelectSymbol?.(result.symbol, result.market)}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold">{result.symbol}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{result.market}</span>
                <span className={`text-xs font-medium ${SENTIMENT_COLORS[result.sentiment]}`}>
                  {SENTIMENT_LABELS[result.sentiment]}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold tabular-nums">${result.price.toFixed(2)}</span>
                <div className="flex items-center gap-1 bg-bb-blue/20 text-bb-blue px-1.5 py-0.5 rounded text-[10px]">
                  <Zap className="h-3 w-3" />
                  {result.score.toFixed(0)}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2 text-xs">
              <div>
                <span className="text-muted-foreground">IV Rank: </span>
                <span className={result.iv_rank > 50 ? "text-bb-amber font-medium" : ""}>
                  {result.iv_rank.toFixed(1)}%
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">IV %ile: </span>
                <span>{result.iv_percentile.toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-muted-foreground">P/C Ratio: </span>
                <span className={result.put_call_ratio > 1 ? "text-bb-red" : "text-bb-green"}>
                  {result.put_call_ratio.toFixed(2)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">Volume: </span>
                <span>{(result.total_volume / 1000).toFixed(0)}K</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Options Scanner</span>
          <Select
            value={market}
            onChange={(e) => setMarket(e.target.value as Market)}
            className="w-20 h-8"
          >
            <option value="US">US</option>
            <option value="JP">JP</option>
            <option value="HK">HK</option>
          </Select>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-4 w-full mb-3">
            <TabsTrigger value="high-iv" className="text-xs gap-1.5">
              <TrendingUp className="h-3.5 w-3.5" />
              High IV
            </TabsTrigger>
            <TabsTrigger value="low-iv" className="text-xs gap-1.5">
              <TrendingDown className="h-3.5 w-3.5" />
              Low IV
            </TabsTrigger>
            <TabsTrigger value="volume" className="text-xs gap-1.5">
              <Activity className="h-3.5 w-3.5" />
              Volume
            </TabsTrigger>
            <TabsTrigger value="custom" className="text-xs gap-1.5">
              <Search className="h-3.5 w-3.5" />
              Custom
            </TabsTrigger>
          </TabsList>

          <TabsContent value="high-iv">
            <p className="text-xs text-muted-foreground mb-3">
              High IV Rank opportunities - good for premium selling strategies
            </p>
            {renderResults(highIVData?.results, highIVLoading)}
          </TabsContent>

          <TabsContent value="low-iv">
            <p className="text-xs text-muted-foreground mb-3">
              Low IV Rank opportunities - good for premium buying strategies
            </p>
            {renderResults(lowIVData?.results, lowIVLoading)}
          </TabsContent>

          <TabsContent value="volume">
            <p className="text-xs text-muted-foreground mb-3">
              High volume activity - potential momentum plays
            </p>
            {renderResults(highVolumeData?.results, highVolumeLoading)}
          </TabsContent>

          <TabsContent value="custom">
            <div className="space-y-3">
              <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">IV Rank Min</label>
                    <Input
                      type="number"
                      placeholder="0"
                      value={customCriteria.iv_rank_min || ""}
                      onChange={(e) =>
                        setCustomCriteria({
                          ...customCriteria,
                          iv_rank_min: e.target.value ? parseFloat(e.target.value) : undefined,
                        })
                      }
                      className="h-8"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">IV Rank Max</label>
                    <Input
                      type="number"
                      placeholder="100"
                      value={customCriteria.iv_rank_max || ""}
                      onChange={(e) =>
                        setCustomCriteria({
                          ...customCriteria,
                          iv_rank_max: e.target.value ? parseFloat(e.target.value) : undefined,
                        })
                      }
                      className="h-8"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Min Volume</label>
                    <Input
                      type="number"
                      placeholder="50000"
                      value={customCriteria.volume_min || ""}
                      onChange={(e) =>
                        setCustomCriteria({
                          ...customCriteria,
                          volume_min: e.target.value ? parseInt(e.target.value) : undefined,
                        })
                      }
                      className="h-8"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Price Range</label>
                    <div className="flex gap-1">
                      <Input
                        type="number"
                        placeholder="Min"
                        value={customCriteria.price_min || ""}
                        onChange={(e) =>
                          setCustomCriteria({
                            ...customCriteria,
                            price_min: e.target.value ? parseFloat(e.target.value) : undefined,
                          })
                        }
                        className="h-8"
                      />
                      <Input
                        type="number"
                        placeholder="Max"
                        value={customCriteria.price_max || ""}
                        onChange={(e) =>
                          setCustomCriteria({
                            ...customCriteria,
                            price_max: e.target.value ? parseFloat(e.target.value) : undefined,
                          })
                        }
                        className="h-8"
                      />
                    </div>
                  </div>
                </div>
                <Button onClick={handleCustomScan} disabled={customScan.isPending} className="w-full mt-2">
                  {customScan.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
                  ) : (
                    <Search className="h-3.5 w-3.5 mr-2" />
                  )}
                  Run Scan
                </Button>
              </div>
              {customScan.data && renderResults(customScan.data.results, false)}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
