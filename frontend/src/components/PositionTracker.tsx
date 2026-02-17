import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Plus, Trash2, X, TrendingUp, TrendingDown, Activity, Clock } from "lucide-react"
import { usePositions, usePortfolioSummary, useCreatePosition, useDeletePosition, useClosePosition } from "@/hooks/useMarketData"
import type { Market, Position, PositionLeg, OptionType, ActionType } from "@/lib/api"

interface PositionTrackerProps {
  className?: string
}

export function PositionTracker({ className }: PositionTrackerProps) {
  const [showAddForm, setShowAddForm] = useState(false)
  const [newPosition, setNewPosition] = useState({
    symbol: "",
    market: "US" as Market,
    strategy_name: "Custom",
    legs: [] as Omit<PositionLeg, "current_premium">[],
  })

  const { data: positions, isLoading } = usePositions()
  const { data: summary } = usePortfolioSummary()
  const createPosition = useCreatePosition()
  const deletePosition = useDeletePosition()
  const closePosition = useClosePosition()

  const addLegToNew = () => {
    setNewPosition({
      ...newPosition,
      legs: [
        ...newPosition.legs,
        {
          option_type: "call" as OptionType,
          action: "buy" as ActionType,
          strike: 100,
          expiration: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
          quantity: 1,
          entry_premium: 5,
        },
      ],
    })
  }

  const updateNewLeg = (index: number, updates: Partial<PositionLeg>) => {
    const newLegs = [...newPosition.legs]
    newLegs[index] = { ...newLegs[index], ...updates }
    setNewPosition({ ...newPosition, legs: newLegs })
  }

  const removeNewLeg = (index: number) => {
    setNewPosition({
      ...newPosition,
      legs: newPosition.legs.filter((_, i) => i !== index),
    })
  }

  const handleCreatePosition = () => {
    if (!newPosition.symbol || newPosition.legs.length === 0) return
    createPosition.mutate(newPosition, {
      onSuccess: () => {
        setShowAddForm(false)
        setNewPosition({
          symbol: "",
          market: "US",
          strategy_name: "Custom",
          legs: [],
        })
      },
    })
  }

  const formatCurrency = (value: number) => {
    return value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Position Tracker</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <span>Position Tracker</span>
          <Button variant="outline" size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? <X className="h-3.5 w-3.5 mr-1" /> : <Plus className="h-3.5 w-3.5 mr-1" />}
            {showAddForm ? "Cancel" : "Add Position"}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Portfolio Summary */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                <Activity className="h-3.5 w-3.5" />
                Open Positions
              </div>
              <span className="text-lg font-bold tabular-nums">{summary.open_positions}</span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Total Value
              </div>
              <span className="text-lg font-bold tabular-nums">{formatCurrency(summary.total_value)}</span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                <TrendingUp className="h-3.5 w-3.5" />
                Unrealized P/L
              </div>
              <span className={`text-lg font-bold tabular-nums ${summary.total_unrealized_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {formatCurrency(summary.total_unrealized_pnl)}
              </span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                Total P/L
              </div>
              <span className={`text-lg font-bold tabular-nums ${summary.total_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {formatCurrency(summary.total_pnl)}
              </span>
            </div>
          </div>
        )}

        {/* Aggregate Greeks */}
        {summary && summary.aggregate_greeks && (
          <div className="grid grid-cols-4 gap-2">
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Delta</div>
              <div className={`font-semibold tabular-nums ${summary.aggregate_greeks.delta >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {summary.aggregate_greeks.delta.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Gamma</div>
              <div className="font-semibold tabular-nums text-bb-blue">{summary.aggregate_greeks.gamma.toFixed(3)}</div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Theta</div>
              <div className={`font-semibold tabular-nums ${summary.aggregate_greeks.theta >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {summary.aggregate_greeks.theta.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-2 bg-muted/30 rounded">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Vega</div>
              <div className="font-semibold tabular-nums text-bb-cyan">{summary.aggregate_greeks.vega.toFixed(2)}</div>
            </div>
          </div>
        )}

        {/* Add Position Form */}
        {showAddForm && (
          <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30">
            <div className="flex gap-2">
              <Input
                placeholder="Symbol (e.g., AAPL)"
                value={newPosition.symbol}
                onChange={(e) => setNewPosition({ ...newPosition, symbol: e.target.value.toUpperCase() })}
                className="w-32 h-8"
              />
              <Select
                value={newPosition.market}
                onChange={(e) => setNewPosition({ ...newPosition, market: e.target.value as Market })}
                className="w-20 h-8"
              >
                <option value="US">US</option>
                <option value="JP">JP</option>
                <option value="HK">HK</option>
              </Select>
              <Input
                placeholder="Strategy name"
                value={newPosition.strategy_name}
                onChange={(e) => setNewPosition({ ...newPosition, strategy_name: e.target.value })}
                className="flex-1 h-8"
              />
            </div>
            {newPosition.legs.map((leg, index) => (
              <div key={index} className="flex items-center gap-2 bg-background p-2 rounded">
                <Select
                  value={leg.action}
                  onChange={(e) => updateNewLeg(index, { action: e.target.value as ActionType })}
                  className="w-20 h-8"
                >
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </Select>
                <Select
                  value={leg.option_type}
                  onChange={(e) => updateNewLeg(index, { option_type: e.target.value as OptionType })}
                  className="w-20 h-8"
                >
                  <option value="call">Call</option>
                  <option value="put">Put</option>
                </Select>
                <Input
                  type="number"
                  placeholder="Strike"
                  value={leg.strike}
                  onChange={(e) => updateNewLeg(index, { strike: parseFloat(e.target.value) || 0 })}
                  className="w-20 h-8"
                />
                <Input
                  type="date"
                  value={leg.expiration}
                  onChange={(e) => updateNewLeg(index, { expiration: e.target.value })}
                  className="w-36 h-8"
                />
                <Input
                  type="number"
                  placeholder="Premium"
                  value={leg.entry_premium}
                  onChange={(e) => updateNewLeg(index, { entry_premium: parseFloat(e.target.value) || 0 })}
                  className="w-20 h-8"
                />
                <Button variant="ghost" size="icon" onClick={() => removeNewLeg(index)}>
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </div>
            ))}
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={addLegToNew}>
                <Plus className="h-3.5 w-3.5 mr-1" /> Add Leg
              </Button>
              <Button
                size="sm"
                onClick={handleCreatePosition}
                disabled={!newPosition.symbol || newPosition.legs.length === 0 || createPosition.isPending}
              >
                {createPosition.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
                Create Position
              </Button>
            </div>
          </div>
        )}

        {/* Positions List */}
        {positions && positions.length > 0 ? (
          <div className="space-y-2 max-h-[480px] overflow-y-auto">
            {positions.filter(p => p.status === "open").map((position) => (
              <div key={position.id} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold">{position.symbol}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{position.market}</span>
                    <span className="text-xs text-muted-foreground">{position.strategy_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold tabular-nums ${position.unrealized_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                      {formatCurrency(position.unrealized_pnl)}
                    </span>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deletePosition.mutate(position.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-destructive" />
                    </Button>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {position.legs.map((leg, i) => (
                    <span
                      key={i}
                      className={`text-[10px] px-1.5 py-0.5 rounded ${
                        leg.action === "buy" ? "bg-bb-green/20 text-bb-green" : "bg-bb-red/20 text-bb-red"
                      }`}
                    >
                      {leg.action === "buy" ? "+" : "-"}{leg.quantity} {leg.option_type.toUpperCase()} ${leg.strike}
                    </span>
                  ))}
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                  <span>Entry: {formatCurrency(position.entry_cost)}</span>
                  <span>Current: {formatCurrency(position.current_value)}</span>
                  <span>Opened: {new Date(position.entry_date).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
            <Activity className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">No open positions</p>
            <p className="text-xs text-muted-foreground mt-1">Add a position to start tracking</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
