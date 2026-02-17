import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Loader2,
  Plus,
  X,
  BookOpen,
  BarChart3,
  TrendingUp,
  TrendingDown,
  Target,
  Percent,
  Award,
  AlertTriangle,
  Calendar,
  Trash2,
} from "lucide-react"
import {
  useJournalTrades,
  useJournalStats,
  useCreateJournalTrade,
  useCloseJournalTrade,
  useDeleteJournalTrade,
} from "@/hooks/useMarketData"
import type { Market, TradeEntry } from "@/lib/api"

interface TradeJournalProps {
  className?: string
}

export function TradeJournal({ className }: TradeJournalProps) {
  const [activeTab, setActiveTab] = useState("trades")
  const [showAddForm, setShowAddForm] = useState(false)
  const [newTrade, setNewTrade] = useState({
    symbol: "",
    market: "US" as Market,
    strategy: "Custom",
    entry_price: 0,
    quantity: 1,
    notes: "",
    tags: [] as string[],
  })
  const [newTag, setNewTag] = useState("")
  const [closingTrade, setClosingTrade] = useState<string | null>(null)
  const [exitPrice, setExitPrice] = useState(0)
  const [exitNotes, setExitNotes] = useState("")
  const [lessons, setLessons] = useState("")

  const { data: trades, isLoading } = useJournalTrades()
  const { data: stats } = useJournalStats()
  const createTrade = useCreateJournalTrade()
  const closeTrade = useCloseJournalTrade()
  const deleteTrade = useDeleteJournalTrade()

  const handleCreateTrade = () => {
    if (!newTrade.symbol || newTrade.entry_price <= 0) return
    createTrade.mutate(newTrade, {
      onSuccess: () => {
        setShowAddForm(false)
        setNewTrade({
          symbol: "",
          market: "US",
          strategy: "Custom",
          entry_price: 0,
          quantity: 1,
          notes: "",
          tags: [],
        })
      },
    })
  }

  const handleCloseTrade = (tradeId: string) => {
    if (exitPrice <= 0) return
    closeTrade.mutate(
      { id: tradeId, request: { exit_price: exitPrice, notes: exitNotes, lessons } },
      {
        onSuccess: () => {
          setClosingTrade(null)
          setExitPrice(0)
          setExitNotes("")
          setLessons("")
        },
      }
    )
  }

  const addTag = () => {
    if (newTag && !newTrade.tags.includes(newTag)) {
      setNewTrade({ ...newTrade, tags: [...newTrade.tags, newTag] })
      setNewTag("")
    }
  }

  const removeTag = (tag: string) => {
    setNewTrade({ ...newTrade, tags: newTrade.tags.filter((t) => t !== tag) })
  }

  const formatCurrency = (value: number) => {
    return value >= 0 ? `$${value.toFixed(2)}` : `-$${Math.abs(value).toFixed(2)}`
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Trade Journal</CardTitle>
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
          <span>Trade Journal</span>
          <Button variant="outline" size="sm" onClick={() => setShowAddForm(!showAddForm)}>
            {showAddForm ? <X className="h-3.5 w-3.5 mr-1" /> : <Plus className="h-3.5 w-3.5 mr-1" />}
            {showAddForm ? "Cancel" : "Log Trade"}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-2 w-full mb-3">
            <TabsTrigger value="trades" className="text-xs gap-1.5">
              <BookOpen className="h-3.5 w-3.5" />
              Trades
            </TabsTrigger>
            <TabsTrigger value="stats" className="text-xs gap-1.5">
              <BarChart3 className="h-3.5 w-3.5" />
              Statistics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trades" className="mt-4">
            {/* Add Trade Form */}
            {showAddForm && (
              <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30 mb-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Input
                    placeholder="Symbol"
                    value={newTrade.symbol}
                    onChange={(e) => setNewTrade({ ...newTrade, symbol: e.target.value.toUpperCase() })}
                    className="h-8"
                  />
                  <Select
                    value={newTrade.market}
                    onChange={(e) => setNewTrade({ ...newTrade, market: e.target.value as Market })}
                    className="h-8"
                  >
                    <option value="US">US</option>
                    <option value="JP">JP</option>
                    <option value="HK">HK</option>
                  </Select>
                  <Input
                    type="number"
                    placeholder="Entry Price"
                    value={newTrade.entry_price || ""}
                    onChange={(e) => setNewTrade({ ...newTrade, entry_price: parseFloat(e.target.value) || 0 })}
                    className="h-8"
                  />
                  <Input
                    type="number"
                    placeholder="Quantity"
                    value={newTrade.quantity || ""}
                    onChange={(e) => setNewTrade({ ...newTrade, quantity: parseInt(e.target.value) || 1 })}
                    className="h-8"
                  />
                </div>
                <Input
                  placeholder="Strategy (e.g., Iron Condor, Covered Call)"
                  value={newTrade.strategy}
                  onChange={(e) => setNewTrade({ ...newTrade, strategy: e.target.value })}
                  className="h-8"
                />
                <Input
                  placeholder="Notes"
                  value={newTrade.notes}
                  onChange={(e) => setNewTrade({ ...newTrade, notes: e.target.value })}
                  className="h-8"
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="Add tag"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && addTag()}
                    className="h-8"
                  />
                  <Button variant="outline" onClick={addTag}>Add</Button>
                </div>
                {newTrade.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {newTrade.tags.map((tag) => (
                      <span
                        key={tag}
                        className="bg-bb-blue/20 text-bb-blue text-[10px] px-1.5 py-0.5 rounded flex items-center gap-1"
                      >
                        {tag}
                        <X className="h-3 w-3 cursor-pointer" onClick={() => removeTag(tag)} />
                      </span>
                    ))}
                  </div>
                )}
                <Button onClick={handleCreateTrade} disabled={createTrade.isPending} className="w-full mt-2">
                  {createTrade.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />}
                  Log Trade
                </Button>
              </div>
            )}

            {/* Trades List */}
            {trades && trades.length > 0 ? (
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {trades.map((trade: TradeEntry) => (
                  <div key={trade.id} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                    {closingTrade === trade.id ? (
                      <div className="space-y-2">
                        <div className="flex gap-2">
                          <Input
                            type="number"
                            placeholder="Exit Price"
                            value={exitPrice || ""}
                            onChange={(e) => setExitPrice(parseFloat(e.target.value) || 0)}
                            className="h-8"
                          />
                          <Button onClick={() => handleCloseTrade(trade.id)} disabled={closeTrade.isPending}>
                            {closeTrade.isPending ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Close"}
                          </Button>
                          <Button variant="outline" onClick={() => setClosingTrade(null)}>Cancel</Button>
                        </div>
                        <Input
                          placeholder="Exit notes"
                          value={exitNotes}
                          onChange={(e) => setExitNotes(e.target.value)}
                          className="h-8"
                        />
                        <Input
                          placeholder="Lessons learned"
                          value={lessons}
                          onChange={(e) => setLessons(e.target.value)}
                          className="h-8"
                        />
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold">{trade.symbol}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{trade.market}</span>
                            <span className="text-xs text-muted-foreground">{trade.strategy}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                              trade.status === "open" ? "bg-bb-blue/20 text-bb-blue" : "bg-bb-muted/20 text-bb-muted"
                            }`}>
                              {trade.status.toUpperCase()}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {trade.pnl !== undefined && trade.pnl !== null && (
                              <span className={`font-semibold tabular-nums ${trade.pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                                {formatCurrency(trade.pnl)}
                                {trade.pnl_percent !== undefined && (
                                  <span className="text-xs ml-1">({trade.pnl_percent.toFixed(1)}%)</span>
                                )}
                              </span>
                            )}
                            {trade.status === "open" && (
                              <Button variant="outline" size="sm" onClick={() => setClosingTrade(trade.id)}>
                                Close
                              </Button>
                            )}
                            <Button variant="ghost" size="icon" onClick={() => deleteTrade.mutate(trade.id)}>
                              <Trash2 className="h-3.5 w-3.5 text-destructive" />
                            </Button>
                          </div>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-muted-foreground">
                          <span>Entry: ${trade.entry_price.toFixed(2)}</span>
                          {trade.exit_price && <span>Exit: ${trade.exit_price.toFixed(2)}</span>}
                          <span>Qty: {trade.quantity}</span>
                          <span><Calendar className="h-3 w-3 inline mr-1" />{new Date(trade.entry_date).toLocaleDateString()}</span>
                        </div>
                        {trade.tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {trade.tags.map((tag) => (
                              <span key={tag} className="bg-bb-blue/20 text-bb-blue text-[10px] px-1.5 py-0.5 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        {trade.notes && <p className="text-xs text-muted-foreground mt-2">{trade.notes}</p>}
                        {trade.lessons && (
                          <p className="text-xs text-bb-amber mt-1">
                            <Award className="h-3 w-3 inline mr-1" />
                            {trade.lessons}
                          </p>
                        )}
                      </>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <BookOpen className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No trades logged yet</p>
                <p className="text-xs text-muted-foreground mt-1">Start logging trades to track performance</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="stats" className="mt-4">
            {stats ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <BarChart3 className="h-3.5 w-3.5" />
                      Total Trades
                    </div>
                    <span className="text-lg font-bold tabular-nums">{stats.total_trades}</span>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <Target className="h-3.5 w-3.5" />
                      Win Rate
                    </div>
                    <span className={`text-lg font-bold tabular-nums ${stats.win_rate >= 50 ? "text-bb-green" : "text-bb-red"}`}>
                      {stats.win_rate.toFixed(1)}%
                    </span>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <Percent className="h-3.5 w-3.5" />
                      Profit Factor
                    </div>
                    <span className={`text-lg font-bold tabular-nums ${stats.profit_factor >= 1 ? "text-bb-green" : "text-bb-red"}`}>
                      {stats.profit_factor === Infinity ? "∞" : stats.profit_factor.toFixed(2)}
                    </span>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                      Total P/L
                    </div>
                    <span className={`text-lg font-bold tabular-nums ${stats.total_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                      {formatCurrency(stats.total_pnl)}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <TrendingUp className="h-3.5 w-3.5" />
                      Avg Win
                    </div>
                    <span className="text-lg font-bold tabular-nums text-bb-green">{formatCurrency(stats.avg_win)}</span>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <TrendingDown className="h-3.5 w-3.5" />
                      Avg Loss
                    </div>
                    <span className="text-lg font-bold tabular-nums text-bb-red">{formatCurrency(stats.avg_loss)}</span>
                  </div>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                      <Calendar className="h-3.5 w-3.5" />
                      Avg Hold
                    </div>
                    <span className="text-lg font-bold tabular-nums">{stats.avg_holding_days.toFixed(1)} days</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-bb-green/10 border border-bb-green/20 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-bb-green text-xs mb-1">
                      <Award className="h-3.5 w-3.5" />
                      Best Trade
                    </div>
                    <span className="text-lg font-bold tabular-nums text-bb-green">{formatCurrency(stats.best_trade)}</span>
                  </div>
                  <div className="bg-bb-red/10 border border-bb-red/20 rounded-lg p-3">
                    <div className="flex items-center gap-2 text-bb-red text-xs mb-1">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      Worst Trade
                    </div>
                    <span className="text-lg font-bold tabular-nums text-bb-red">{formatCurrency(stats.worst_trade)}</span>
                  </div>
                </div>

                <div className="text-center text-sm text-muted-foreground pt-2">
                  <span className="text-bb-green">{stats.winning_trades} wins</span>
                  {" / "}
                  <span className="text-bb-red">{stats.losing_trades} losses</span>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <BarChart3 className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No statistics available</p>
                <p className="text-xs text-muted-foreground mt-1">Close some trades to see stats</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
