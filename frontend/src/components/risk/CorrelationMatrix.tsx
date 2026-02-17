import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Loader2, Grid3X3, Plus, X } from "lucide-react"
import { useCorrelationMatrix } from "@/hooks/useMarketData"

interface CorrelationMatrixProps {
  initialSymbols?: string[]
  className?: string
}

export function CorrelationMatrix({
  initialSymbols = ["AAPL", "MSFT", "GOOGL", "AMZN"],
  className
}: CorrelationMatrixProps) {
  const [symbols, setSymbols] = useState<string[]>(initialSymbols)
  const [newSymbol, setNewSymbol] = useState("")
  const [periodDays, setPeriodDays] = useState(30)

  const { data, isLoading } = useCorrelationMatrix(symbols, periodDays, symbols.length >= 2)

  const addSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()])
      setNewSymbol("")
    }
  }

  const removeSymbol = (symbol: string) => {
    setSymbols(symbols.filter(s => s !== symbol))
  }

  const getCorrelationColor = (value: number) => {
    if (value >= 0.7) return "bg-bb-green/50"
    if (value >= 0.3) return "bg-bb-green/20"
    if (value >= -0.3) return "bg-bb-muted/20"
    if (value >= -0.7) return "bg-bb-red/20"
    return "bg-bb-red/50"
  }

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Correlation Matrix</CardTitle>
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
          <div className="flex items-center gap-2">
            <Grid3X3 className="h-4 w-4" />
            Correlation Matrix
          </div>
          <Select
            value={periodDays.toString()}
            onChange={(e) => setPeriodDays(parseInt(e.target.value))}
            className="w-24 h-8"
          >
            <option value="7">7 days</option>
            <option value="14">14 days</option>
            <option value="30">30 days</option>
            <option value="60">60 days</option>
            <option value="90">90 days</option>
          </Select>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Symbol Input */}
        <div className="flex gap-2">
          <Input
            placeholder="Add symbol"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === "Enter" && addSymbol()}
            className="flex-1 h-8"
          />
          <Button onClick={addSymbol} disabled={!newSymbol}>
            <Plus className="h-3.5 w-3.5" />
          </Button>
        </div>

        {/* Symbol Tags */}
        <div className="flex flex-wrap gap-1">
          {symbols.map((symbol) => (
            <span
              key={symbol}
              className="bg-muted px-2 py-1 rounded text-sm flex items-center gap-1"
            >
              {symbol}
              <X
                className="h-3 w-3 cursor-pointer hover:text-destructive"
                onClick={() => removeSymbol(symbol)}
              />
            </span>
          ))}
        </div>

        {/* Matrix */}
        {data && data.matrix.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="p-2"></th>
                    {data.symbols.map((symbol) => (
                      <th key={symbol} className="p-2 text-center font-bold">{symbol}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.matrix.map((row, i) => (
                    <tr key={data.symbols[i]}>
                      <td className="p-2 font-bold">{data.symbols[i]}</td>
                      {row.map((value, j) => (
                        <td
                          key={`${i}-${j}`}
                          className={`p-2 text-center tabular-nums ${getCorrelationColor(value)} ${i === j ? "font-bold" : ""}`}
                        >
                          {value.toFixed(2)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Top Correlations */}
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Notable Correlations:</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {data.pairs
                  .filter(p => p.symbol1 !== p.symbol2)
                  .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
                  .slice(0, 6)
                  .map((pair, i) => (
                    <div
                      key={i}
                      className={`p-2 rounded text-xs ${pair.correlation > 0 ? "bg-bb-green/20" : "bg-bb-red/20"}`}
                    >
                      <span className="font-medium">{pair.symbol1}</span>
                      <span className="text-muted-foreground"> - </span>
                      <span className="font-medium">{pair.symbol2}</span>
                      <span className={`ml-2 font-bold tabular-nums ${pair.correlation > 0 ? "text-bb-green" : "text-bb-red"}`}>
                        {pair.correlation.toFixed(2)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>

            {/* Legend */}
            <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground pt-2 border-t">
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-bb-green/50 rounded"></div>
                Strong +
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-bb-green/20 rounded"></div>
                Moderate +
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-bb-muted/20 rounded"></div>
                Weak
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-bb-red/20 rounded"></div>
                Moderate -
              </span>
              <span className="flex items-center gap-1">
                <div className="w-4 h-4 bg-bb-red/50 rounded"></div>
                Strong -
              </span>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Grid3X3 className="h-8 w-8 mb-2 opacity-50" />
            <p className="text-sm">Add at least 2 symbols</p>
            <p className="text-xs text-muted-foreground mt-1">to see correlations</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
