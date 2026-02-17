import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Loader2,
  DollarSign,
  TrendingUp,
  TrendingDown,
  History,
  Briefcase,
  RefreshCw,
  ShoppingCart,
} from "lucide-react"
import {
  useDefaultPaperAccount,
  usePlacePaperOrder,
  useResetPaperAccount,
} from "@/hooks/useMarketData"
import type { Market, OrderSide, PaperOrder, PaperPosition } from "@/lib/api"

interface PaperTradingProps {
  className?: string
}

export function PaperTrading({ className }: PaperTradingProps) {
  const [activeTab, setActiveTab] = useState("trade")
  const [orderForm, setOrderForm] = useState({
    symbol: "AAPL",
    market: "US" as Market,
    side: "buy" as OrderSide,
    quantity: 100,
    limit_price: undefined as number | undefined,
  })

  const { data: account, isLoading, refetch } = useDefaultPaperAccount()
  const placeOrder = usePlacePaperOrder()
  const resetAccount = useResetPaperAccount()

  const handlePlaceOrder = () => {
    if (!account || !orderForm.symbol || orderForm.quantity <= 0) return
    placeOrder.mutate(
      {
        account_id: account.id,
        symbol: orderForm.symbol.toUpperCase(),
        market: orderForm.market,
        side: orderForm.side,
        quantity: orderForm.quantity,
        order_type: "market",
        limit_price: orderForm.limit_price,
      },
      {
        onSuccess: () => {
          refetch()
        },
      }
    )
  }

  const handleReset = () => {
    if (!account) return
    if (confirm("Are you sure you want to reset this account? All positions and orders will be cleared.")) {
      resetAccount.mutate(account.id)
    }
  }

  const formatCurrency = (value: number) => {
    return value >= 0 ? `$${value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : `-$${Math.abs(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Paper Trading</CardTitle>
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
          <span>Paper Trading</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
            <Button variant="outline" size="sm" onClick={handleReset}>
              Reset
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Account Summary */}
        {account && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                <DollarSign className="h-3.5 w-3.5" />
                Cash
              </div>
              <span className="text-lg font-bold tabular-nums">{formatCurrency(account.cash)}</span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                <Briefcase className="h-3.5 w-3.5" />
                Total Value
              </div>
              <span className="text-lg font-bold tabular-nums">{formatCurrency(account.total_value)}</span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                <TrendingUp className="h-3.5 w-3.5" />
                P/L
              </div>
              <span className={`text-lg font-bold tabular-nums ${account.total_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {formatCurrency(account.total_pnl)}
              </span>
            </div>
            <div className="bg-muted/50 rounded-lg p-3">
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">
                P/L %
              </div>
              <span className={`text-lg font-bold tabular-nums ${account.total_pnl_percent >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                {formatPercent(account.total_pnl_percent)}
              </span>
            </div>
          </div>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-3 w-full mb-3">
            <TabsTrigger value="trade" className="text-xs gap-1.5">
              <ShoppingCart className="h-3.5 w-3.5" />
              Trade
            </TabsTrigger>
            <TabsTrigger value="positions" className="text-xs gap-1.5">
              <Briefcase className="h-3.5 w-3.5" />
              Positions
            </TabsTrigger>
            <TabsTrigger value="orders" className="text-xs gap-1.5">
              <History className="h-3.5 w-3.5" />
              Orders
            </TabsTrigger>
          </TabsList>

          <TabsContent value="trade" className="space-y-3 mt-4">
            <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Input
                  placeholder="Symbol"
                  value={orderForm.symbol}
                  onChange={(e) => setOrderForm({ ...orderForm, symbol: e.target.value.toUpperCase() })}
                  className="h-8"
                />
                <Select
                  value={orderForm.market}
                  onChange={(e) => setOrderForm({ ...orderForm, market: e.target.value as Market })}
                  className="h-8"
                >
                  <option value="US">US</option>
                  <option value="JP">JP</option>
                  <option value="HK">HK</option>
                </Select>
                <Select
                  value={orderForm.side}
                  onChange={(e) => setOrderForm({ ...orderForm, side: e.target.value as OrderSide })}
                  className="h-8"
                >
                  <option value="buy">Buy</option>
                  <option value="sell">Sell</option>
                </Select>
                <Input
                  type="number"
                  placeholder="Quantity"
                  value={orderForm.quantity}
                  onChange={(e) => setOrderForm({ ...orderForm, quantity: parseInt(e.target.value) || 0 })}
                  className="h-8"
                />
              </div>
              <Button
                className="w-full mt-2"
                onClick={handlePlaceOrder}
                disabled={placeOrder.isPending || !orderForm.symbol || orderForm.quantity <= 0}
              >
                {placeOrder.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-2" />
                ) : orderForm.side === "buy" ? (
                  <TrendingUp className="h-3.5 w-3.5 mr-2" />
                ) : (
                  <TrendingDown className="h-3.5 w-3.5 mr-2" />
                )}
                {orderForm.side === "buy" ? "Buy" : "Sell"} {orderForm.quantity} {orderForm.symbol}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="positions" className="mt-4">
            {account && account.positions.length > 0 ? (
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {account.positions.map((position: PaperPosition, index: number) => (
                  <div key={index} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold">{position.symbol}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted">{position.market}</span>
                        <span className="text-sm text-muted-foreground">{position.quantity} shares</span>
                      </div>
                      <span className={`font-semibold tabular-nums ${position.unrealized_pnl >= 0 ? "text-bb-green" : "text-bb-red"}`}>
                        {formatCurrency(position.unrealized_pnl)}
                      </span>
                    </div>
                    <div className="flex gap-4 text-xs text-muted-foreground">
                      <span>Avg: ${position.avg_entry_price.toFixed(2)}</span>
                      <span>Current: ${position.current_price.toFixed(2)}</span>
                      <span>Value: {formatCurrency(position.current_price * position.quantity)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <Briefcase className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No open positions</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="orders" className="mt-4">
            {account && account.orders.length > 0 ? (
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {account.orders.slice().reverse().map((order: PaperOrder) => (
                  <div key={order.id} className="border border-border rounded-lg p-3 bg-muted/20 hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                          order.side === "buy" ? "bg-bb-green/20 text-bb-green" : "bg-bb-red/20 text-bb-red"
                        }`}>
                          {order.side.toUpperCase()}
                        </span>
                        <span className="font-bold">{order.symbol}</span>
                        <span className="text-sm text-muted-foreground">{order.quantity} @ ${order.filled_price?.toFixed(2) || "Market"}</span>
                      </div>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        order.status === "filled" ? "bg-bb-green/20 text-bb-green" :
                        order.status === "rejected" ? "bg-bb-red/20 text-bb-red" :
                        "bg-bb-amber/20 text-bb-amber"
                      }`}>
                        {order.status.toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {new Date(order.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                <History className="h-8 w-8 mb-2 opacity-50" />
                <p className="text-sm">No orders yet</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
