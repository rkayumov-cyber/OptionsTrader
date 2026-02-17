import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, Calculator, Target, TrendingUp, TrendingDown } from "lucide-react"
import { useCalculateProbability, useQuote } from "@/hooks/useMarketData"
import type { Market } from "@/lib/api"

interface ProbabilityCalculatorProps {
  symbol?: string
  market?: Market
  className?: string
}

export function ProbabilityCalculator({
  symbol: initialSymbol = "AAPL",
  market: initialMarket = "US",
  className
}: ProbabilityCalculatorProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [market] = useState<Market>(initialMarket)
  const [strike, setStrike] = useState(150)
  const [dte, setDte] = useState(30)
  const [iv, setIv] = useState(30)

  const { data: quote } = useQuote(symbol, market)
  const { data: probability, isLoading, refetch } = useCalculateProbability(
    symbol, market, strike, dte, iv, undefined, undefined, false
  )

  const handleCalculate = () => {
    refetch()
  }

  const formatPercent = (value: number) => `${value.toFixed(1)}%`
  const formatCurrency = (value: number) => `$${value.toFixed(2)}`

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Calculator className="h-4 w-4" />
          Probability Calculator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="border border-border rounded-lg p-4 space-y-3 bg-muted/30">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Input
              placeholder="Symbol"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="h-8"
            />
            <Input
              type="number"
              placeholder="Strike"
              value={strike}
              onChange={(e) => setStrike(parseFloat(e.target.value) || 0)}
              className="h-8"
            />
            <Input
              type="number"
              placeholder="DTE"
              value={dte}
              onChange={(e) => setDte(parseInt(e.target.value) || 0)}
              className="h-8"
            />
            <Input
              type="number"
              placeholder="IV %"
              value={iv}
              onChange={(e) => setIv(parseFloat(e.target.value) || 0)}
              className="h-8"
            />
            <Button onClick={handleCalculate} disabled={isLoading}>
              {isLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : "Calculate"}
            </Button>
          </div>
        </div>

        {quote && (
          <div className="text-sm text-muted-foreground">
            Current Price: <span className="font-semibold tabular-nums">{formatCurrency(quote.price)}</span>
          </div>
        )}

        {probability && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-bb-green/10 border border-bb-green/20 rounded-lg p-4">
                <div className="flex items-center gap-2 text-bb-green text-sm mb-1">
                  <TrendingUp className="h-4 w-4" />
                  Probability Above {formatCurrency(strike)}
                </div>
                <span className="text-2xl font-bold tabular-nums text-bb-green">
                  {formatPercent(probability.probability_above)}
                </span>
              </div>
              <div className="bg-bb-red/10 border border-bb-red/20 rounded-lg p-4">
                <div className="flex items-center gap-2 text-bb-red text-sm mb-1">
                  <TrendingDown className="h-4 w-4" />
                  Probability Below {formatCurrency(strike)}
                </div>
                <span className="text-2xl font-bold tabular-nums text-bb-red">
                  {formatPercent(probability.probability_below)}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1 flex items-center gap-2">
                  <Target className="h-3.5 w-3.5" />
                  Expected Move
                </div>
                <span className="text-lg font-bold tabular-nums">
                  ±{formatCurrency(probability.expected_move)}
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">1 Std Dev Range</div>
                <span className="text-sm font-semibold tabular-nums">
                  {formatCurrency(probability.one_std_range[0])} - {formatCurrency(probability.one_std_range[1])}
                </span>
              </div>
              <div className="bg-muted/50 rounded-lg p-3">
                <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">2 Std Dev Range</div>
                <span className="text-sm font-semibold tabular-nums">
                  {formatCurrency(probability.two_std_range[0])} - {formatCurrency(probability.two_std_range[1])}
                </span>
              </div>
            </div>

            <div className="text-xs text-muted-foreground text-center">
              Based on {dte} DTE and {iv}% implied volatility
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
