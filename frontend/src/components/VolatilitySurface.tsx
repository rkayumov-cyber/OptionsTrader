import { useMemo, useState } from "react"
import { RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useVolatilitySurface } from "@/hooks/useMarketData"
import { formatPercent, cn } from "@/lib/utils"
import type { Market } from "@/lib/api"

interface VolatilitySurfaceProps {
  symbol: string
  market: Market
}

function getColorForIV(iv: number): string {
  // Color scale from blue (low IV) to red (high IV)
  if (iv <= 0) return "bg-bb-muted/20"
  if (iv < 0.15) return "bg-bb-blue/20"
  if (iv < 0.20) return "bg-bb-blue/40"
  if (iv < 0.25) return "bg-bb-green/20"
  if (iv < 0.30) return "bg-bb-green/40"
  if (iv < 0.35) return "bg-bb-amber/20"
  if (iv < 0.40) return "bg-bb-amber/40"
  if (iv < 0.50) return "bg-bb-orange/40"
  if (iv < 0.60) return "bg-bb-orange/60"
  return "bg-bb-red/60"
}

export function VolatilitySurface({ symbol, market }: VolatilitySurfaceProps) {
  const [optionType, setOptionType] = useState<"calls" | "puts">("calls")

  const { data: surface, isLoading, isError } = useVolatilitySurface(symbol, market, !!symbol)

  const ivData = useMemo(() => {
    if (!surface) return null
    return optionType === "calls" ? surface.call_ivs : surface.put_ivs
  }, [surface, optionType])

  // Calculate IV statistics
  const ivStats = useMemo(() => {
    if (!ivData) return null
    const allIVs = ivData.flat().filter((iv) => iv > 0)
    if (allIVs.length === 0) return null
    return {
      min: Math.min(...allIVs),
      max: Math.max(...allIVs),
      avg: allIVs.reduce((a, b) => a + b, 0) / allIVs.length,
    }
  }, [ivData])

  if (!symbol) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Volatility Surface</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            Search for a symbol to view volatility surface
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Volatility Surface - {symbol}</CardTitle>
          <Tabs value={optionType} onValueChange={(v) => setOptionType(v as "calls" | "puts")}>
            <TabsList>
              <TabsTrigger value="calls">Calls</TabsTrigger>
              <TabsTrigger value="puts">Puts</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {isError && (
          <div className="text-center py-8 text-destructive">
            Failed to fetch volatility surface
          </div>
        )}

        {surface && ivData && !isLoading && (
          <div className="space-y-4">
            {/* IV Statistics */}
            {ivStats && (
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Min IV: </span>
                  <span className="font-medium">{formatPercent(ivStats.min)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Avg IV: </span>
                  <span className="font-medium">{formatPercent(ivStats.avg)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Max IV: </span>
                  <span className="font-medium">{formatPercent(ivStats.max)}</span>
                </div>
              </div>
            )}

            {/* Heatmap */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    <th className="py-2 px-1 text-left">Exp / Strike</th>
                    {surface.strikes.map((strike) => (
                      <th key={strike} className="py-2 px-1 text-center">
                        {strike.toFixed(0)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {surface.expirations.map((exp, expIdx) => (
                    <tr key={exp}>
                      <td className="py-1 px-1 font-medium whitespace-nowrap">{exp}</td>
                      {surface.strikes.map((strike, strikeIdx) => {
                        const iv = ivData[expIdx]?.[strikeIdx] || 0
                        return (
                          <td
                            key={`${exp}-${strike}`}
                            className={cn(
                              "py-1 px-1 text-center cursor-default transition-colors",
                              getColorForIV(iv)
                            )}
                            title={`Strike: ${strike}, Exp: ${exp}, IV: ${formatPercent(iv)}`}
                          >
                            {iv > 0 ? (iv * 100).toFixed(1) : "-"}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Color Legend */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-muted-foreground">IV Scale:</span>
              <div className="flex gap-1">
                <div className="w-6 h-4 bg-bb-blue/30" title="< 15%"></div>
                <div className="w-6 h-4 bg-bb-green/30" title="20-30%"></div>
                <div className="w-6 h-4 bg-bb-amber/30" title="30-40%"></div>
                <div className="w-6 h-4 bg-bb-orange/50" title="40-60%"></div>
                <div className="w-6 h-4 bg-bb-red/60" title="> 60%"></div>
              </div>
              <span className="text-muted-foreground ml-2">Low → High</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
