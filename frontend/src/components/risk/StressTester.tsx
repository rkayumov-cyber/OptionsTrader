import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, AlertTriangle, Zap, Play } from "lucide-react"
import { useRunStressTest, usePortfolioSummary } from "@/hooks/useMarketData"
import type { StressScenario, StressResult } from "@/lib/api"

interface StressTesterProps {
  className?: string
}

const PRESET_SCENARIOS: StressScenario[] = [
  { name: "Market Crash (-20%)", price_change_percent: -20, iv_change_percent: 50, time_decay_days: 0 },
  { name: "Correction (-10%)", price_change_percent: -10, iv_change_percent: 30, time_decay_days: 0 },
  { name: "Small Pullback (-5%)", price_change_percent: -5, iv_change_percent: 15, time_decay_days: 0 },
  { name: "Flat + Time Decay", price_change_percent: 0, iv_change_percent: 0, time_decay_days: 7 },
  { name: "Rally (+5%)", price_change_percent: 5, iv_change_percent: -10, time_decay_days: 0 },
  { name: "Strong Rally (+10%)", price_change_percent: 10, iv_change_percent: -20, time_decay_days: 0 },
  { name: "VIX Spike (+50% IV)", price_change_percent: 0, iv_change_percent: 50, time_decay_days: 0 },
  { name: "IV Crush (-30% IV)", price_change_percent: 0, iv_change_percent: -30, time_decay_days: 0 },
]

export function StressTester({ className }: StressTesterProps) {
  const [customScenario, setCustomScenario] = useState<StressScenario>({
    name: "Custom",
    price_change_percent: 0,
    iv_change_percent: 0,
    time_decay_days: 0,
  })
  const [selectedScenarios, setSelectedScenarios] = useState<StressScenario[]>(PRESET_SCENARIOS.slice(0, 4))

  const { data: portfolio } = usePortfolioSummary()
  const stressTest = useRunStressTest()

  const runTest = () => {
    stressTest.mutate(selectedScenarios)
  }

  const toggleScenario = (scenario: StressScenario) => {
    const exists = selectedScenarios.find(s => s.name === scenario.name)
    if (exists) {
      setSelectedScenarios(selectedScenarios.filter(s => s.name !== scenario.name))
    } else {
      setSelectedScenarios([...selectedScenarios, scenario])
    }
  }

  const addCustomScenario = () => {
    if (customScenario.name && !selectedScenarios.find(s => s.name === customScenario.name)) {
      setSelectedScenarios([...selectedScenarios, { ...customScenario }])
      setCustomScenario({
        name: "Custom",
        price_change_percent: 0,
        iv_change_percent: 0,
        time_decay_days: 0,
      })
    }
  }

  const formatCurrency = (value: number) => {
    return value >= 0 ? `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `-$${Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(1)}%`
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Stress Testing
          </div>
          <Button onClick={runTest} disabled={stressTest.isPending || selectedScenarios.length === 0}>
            {stressTest.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
            ) : (
              <Play className="h-3.5 w-3.5 mr-2" />
            )}
            Run Test
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Portfolio Value */}
        {portfolio && (
          <div className="bg-muted/50 rounded-lg p-3 flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Current Portfolio Value</span>
            <span className="text-lg font-bold tabular-nums">{formatCurrency(portfolio.total_value)}</span>
          </div>
        )}

        {/* Preset Scenarios */}
        <div>
          <h4 className="text-sm font-semibold mb-2">Select Scenarios:</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {PRESET_SCENARIOS.map((scenario) => {
              const isSelected = selectedScenarios.find(s => s.name === scenario.name)
              return (
                <button
                  key={scenario.name}
                  onClick={() => toggleScenario(scenario)}
                  className={`p-2 rounded-lg text-xs text-left border transition-colors ${
                    isSelected
                      ? "bg-primary/20 border-primary"
                      : "bg-muted/30 border-transparent hover:bg-muted/50"
                  }`}
                >
                  <div className="font-medium mb-1">{scenario.name}</div>
                  <div className="text-muted-foreground">
                    {scenario.price_change_percent !== 0 && (
                      <span className={scenario.price_change_percent > 0 ? "text-bb-green" : "text-bb-red"}>
                        Price: {formatPercent(scenario.price_change_percent)}
                      </span>
                    )}
                    {scenario.iv_change_percent !== 0 && (
                      <span className="ml-2">IV: {formatPercent(scenario.iv_change_percent)}</span>
                    )}
                    {scenario.time_decay_days > 0 && (
                      <span className="ml-2">{scenario.time_decay_days}d decay</span>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {/* Custom Scenario */}
        <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30">
          <h4 className="text-sm font-semibold">Custom Scenario:</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Input
              placeholder="Name"
              value={customScenario.name}
              onChange={(e) => setCustomScenario({ ...customScenario, name: e.target.value })}
              className="h-8"
            />
            <div>
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Price %</label>
              <Input
                type="number"
                value={customScenario.price_change_percent}
                onChange={(e) => setCustomScenario({ ...customScenario, price_change_percent: parseFloat(e.target.value) || 0 })}
                className="h-8"
              />
            </div>
            <div>
              <label className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">IV %</label>
              <Input
                type="number"
                value={customScenario.iv_change_percent}
                onChange={(e) => setCustomScenario({ ...customScenario, iv_change_percent: parseFloat(e.target.value) || 0 })}
                className="h-8"
              />
            </div>
            <div className="flex items-end">
              <Button onClick={addCustomScenario} className="w-full">Add</Button>
            </div>
          </div>
        </div>

        {/* Results */}
        {stressTest.data && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold">Results:</h4>
            <div className="space-y-2">
              {stressTest.data.results.map((result: StressResult, i: number) => (
                <div key={i} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{result.scenario.name}</span>
                    <div className="flex items-center gap-2">
                      <span className={`text-lg font-bold tabular-nums ${result.portfolio_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                        {formatCurrency(result.portfolio_pnl)}
                      </span>
                      <span className={`text-sm tabular-nums ${result.portfolio_pnl_percent >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                        ({formatPercent(result.portfolio_pnl_percent)})
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Price: {formatPercent(result.scenario.price_change_percent)} |
                    IV: {formatPercent(result.scenario.iv_change_percent)}
                    {result.scenario.time_decay_days > 0 && ` | Time: ${result.scenario.time_decay_days}d`}
                  </div>
                  {result.position_impacts.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {result.position_impacts.map((impact, j) => (
                        <span
                          key={j}
                          className={`text-[10px] px-1.5 py-0.5 rounded tabular-nums ${impact.pnl >= 0 ? "bg-bb-green/20 text-bb-green" : "bg-bb-red/20 text-bb-red"}`}
                        >
                          {impact.symbol}: {formatCurrency(impact.pnl)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Summary */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t">
              <div className="bg-bb-red/10 border border-bb-red/20 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-bb-red mb-1">Worst Case</div>
                <span className="text-lg font-bold tabular-nums text-bb-red">
                  {formatCurrency(Math.min(...stressTest.data.results.map(r => r.portfolio_pnl)))}
                </span>
              </div>
              <div className="bg-bb-green/10 border border-bb-green/20 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-bb-green mb-1">Best Case</div>
                <span className="text-lg font-bold tabular-nums text-bb-green">
                  {formatCurrency(Math.max(...stressTest.data.results.map(r => r.portfolio_pnl)))}
                </span>
              </div>
            </div>
          </div>
        )}

        {!stressTest.data && !stressTest.isPending && (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Zap className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Select scenarios and run test</p>
            <p className="text-xs text-muted-foreground mt-1">to see potential portfolio impact</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
