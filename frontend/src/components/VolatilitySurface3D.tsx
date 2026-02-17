import { useState, useMemo } from "react"
import Plot from "react-plotly.js"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Loader2, RotateCcw, Activity } from "lucide-react"
import { useVolatilitySurface } from "@/hooks/useMarketData"
import type { Market } from "@/lib/api"

interface VolatilitySurface3DProps {
  initialSymbol?: string
  initialMarket?: Market
  className?: string
}

type SurfaceType = "calls" | "puts" | "both"

export function VolatilitySurface3D({
  initialSymbol = "SPY",
  initialMarket = "US",
  className,
}: VolatilitySurface3DProps) {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [inputSymbol, setInputSymbol] = useState(initialSymbol)
  const [market] = useState<Market>(initialMarket)
  const [surfaceType, setSurfaceType] = useState<SurfaceType>("calls")

  const { data: surface, isLoading, error, refetch } = useVolatilitySurface(symbol, market)

  const handleSymbolChange = () => {
    if (inputSymbol.trim()) {
      setSymbol(inputSymbol.trim().toUpperCase())
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSymbolChange()
    }
  }

  // Transform data for Plotly 3D surface
  const plotData = useMemo(() => {
    if (!surface) return []

    const { strikes, expirations, call_ivs, put_ivs } = surface

    // Convert expirations to days (approximate)
    const today = new Date()
    const daysToExpiry = expirations.map(exp => {
      const expDate = new Date(exp)
      return Math.max(1, Math.round((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)))
    })

    // Create surfaces based on selection
    const surfaces: Plotly.Data[] = []

    if (surfaceType === "calls" || surfaceType === "both") {
      // Transpose call_ivs for Plotly (it expects z[y][x])
      const callZ = call_ivs.map(row => row.map(v => v * 100)) // Convert to percentage

      surfaces.push({
        type: "surface",
        x: strikes,
        y: daysToExpiry,
        z: callZ,
        colorscale: [
          [0, "rgb(0, 100, 0)"],      // Low IV - dark green
          [0.25, "rgb(50, 205, 50)"], // Light green
          [0.5, "rgb(255, 255, 0)"],  // Yellow
          [0.75, "rgb(255, 165, 0)"], // Orange
          [1, "rgb(255, 0, 0)"],      // High IV - red
        ],
        opacity: surfaceType === "both" ? 0.8 : 1,
        name: "Call IV",
        showscale: true,
        colorbar: {
          title: { text: "IV (%)", side: "right" },
          x: 1.02,
          len: 0.9,
        },
        hovertemplate:
          "Strike: $%{x}<br>" +
          "DTE: %{y} days<br>" +
          "Call IV: %{z:.1f}%<extra></extra>",
      } as Plotly.Data)
    }

    if (surfaceType === "puts" || surfaceType === "both") {
      const putZ = put_ivs.map(row => row.map(v => v * 100)) // Convert to percentage

      surfaces.push({
        type: "surface",
        x: strikes,
        y: daysToExpiry,
        z: putZ,
        colorscale: [
          [0, "rgb(0, 0, 100)"],      // Low IV - dark blue
          [0.25, "rgb(65, 105, 225)"], // Royal blue
          [0.5, "rgb(138, 43, 226)"], // Blue violet
          [0.75, "rgb(255, 20, 147)"], // Deep pink
          [1, "rgb(255, 0, 0)"],      // High IV - red
        ],
        opacity: surfaceType === "both" ? 0.6 : 1,
        name: "Put IV",
        showscale: surfaceType !== "calls",
        colorbar: surfaceType === "both" ? {
          title: { text: "Put IV (%)", side: "right" },
          x: 1.15,
          len: 0.9,
        } : {
          title: { text: "IV (%)", side: "right" },
          x: 1.02,
          len: 0.9,
        },
        hovertemplate:
          "Strike: $%{x}<br>" +
          "DTE: %{y} days<br>" +
          "Put IV: %{z:.1f}%<extra></extra>",
      } as Plotly.Data)
    }

    return surfaces
  }, [surface, surfaceType])

  // Calculate IV statistics
  const ivStats = useMemo(() => {
    if (!surface) return null

    const allCallIVs = surface.call_ivs.flat().filter(v => v > 0)
    const allPutIVs = surface.put_ivs.flat().filter(v => v > 0)

    const callMin = Math.min(...allCallIVs) * 100
    const callMax = Math.max(...allCallIVs) * 100
    const callAvg = (allCallIVs.reduce((a, b) => a + b, 0) / allCallIVs.length) * 100

    const putMin = Math.min(...allPutIVs) * 100
    const putMax = Math.max(...allPutIVs) * 100
    const putAvg = (allPutIVs.reduce((a, b) => a + b, 0) / allPutIVs.length) * 100

    return {
      callMin: callMin.toFixed(1),
      callMax: callMax.toFixed(1),
      callAvg: callAvg.toFixed(1),
      putMin: putMin.toFixed(1),
      putMax: putMax.toFixed(1),
      putAvg: putAvg.toFixed(1),
      skew: ((putAvg - callAvg)).toFixed(1),
    }
  }, [surface])

  const layout: Partial<Plotly.Layout> = {
    autosize: true,
    height: 500,
    margin: { l: 0, r: 0, t: 30, b: 0 },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    scene: {
      xaxis: {
        title: { text: "Strike ($)", font: { size: 12 } },
        gridcolor: "rgba(128,128,128,0.3)",
        showbackground: true,
        backgroundcolor: "rgba(30,30,30,0.8)",
      },
      yaxis: {
        title: { text: "Days to Expiry", font: { size: 12 } },
        gridcolor: "rgba(128,128,128,0.3)",
        showbackground: true,
        backgroundcolor: "rgba(30,30,30,0.8)",
      },
      zaxis: {
        title: { text: "IV (%)", font: { size: 12 } },
        gridcolor: "rgba(128,128,128,0.3)",
        showbackground: true,
        backgroundcolor: "rgba(30,30,30,0.8)",
      },
      camera: {
        eye: { x: 1.5, y: 1.5, z: 1.2 },
      },
      aspectratio: { x: 1.2, y: 1, z: 0.8 },
    },
    font: {
      color: "rgba(200,200,200,1)",
    },
  }

  const config: Partial<Plotly.Config> = {
    displayModeBar: true,
    modeBarButtonsToRemove: ["toImage", "sendDataToCloud"],
    displaylogo: false,
    responsive: true,
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            <span>Volatility Surface</span>
          </div>
          <div className="flex items-center gap-2">
            <Input
              type="text"
              value={inputSymbol}
              onChange={(e) => setInputSymbol(e.target.value.toUpperCase())}
              onKeyDown={handleKeyDown}
              onBlur={handleSymbolChange}
              className="w-24 h-8 uppercase"
              placeholder="Symbol"
            />
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => refetch()}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Surface Type Toggle */}
        <div className="flex items-center gap-2">
          <Button
            variant={surfaceType === "calls" ? "default" : "outline"}
            size="sm"
            onClick={() => setSurfaceType("calls")}
          >
            Calls
          </Button>
          <Button
            variant={surfaceType === "puts" ? "default" : "outline"}
            size="sm"
            onClick={() => setSurfaceType("puts")}
          >
            Puts
          </Button>
          <Button
            variant={surfaceType === "both" ? "default" : "outline"}
            size="sm"
            onClick={() => setSurfaceType("both")}
          >
            Both
          </Button>

          {/* IV Stats */}
          {ivStats && (
            <div className="ml-auto flex items-center gap-4 text-xs text-muted-foreground">
              {surfaceType !== "puts" && (
                <span>
                  Call IV: {ivStats.callMin}% - {ivStats.callMax}% (avg {ivStats.callAvg}%)
                </span>
              )}
              {surfaceType !== "calls" && (
                <span>
                  Put IV: {ivStats.putMin}% - {ivStats.putMax}% (avg {ivStats.putAvg}%)
                </span>
              )}
              <span className={Number(ivStats.skew) > 0 ? "text-bb-red" : "text-bb-green"}>
                Skew: {ivStats.skew}%
              </span>
            </div>
          )}
        </div>

        {/* 3D Surface */}
        {isLoading ? (
          <div className="flex items-center justify-center h-[500px]">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-[500px] text-destructive">
            <p>Error loading volatility surface</p>
          </div>
        ) : plotData.length > 0 ? (
          <div className="rounded-lg overflow-hidden border border-border">
            <Plot
              data={plotData}
              layout={layout}
              config={config}
              style={{ width: "100%", height: "500px" }}
              useResizeHandler
            />
          </div>
        ) : (
          <div className="flex items-center justify-center h-[500px] text-muted-foreground">
            <p>No volatility data available for {symbol}</p>
          </div>
        )}

        {/* Legend / Instructions */}
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Drag to rotate | Scroll to zoom | Double-click to reset</span>
          {surface && (
            <span>
              {surface.strikes.length} strikes x {surface.expirations.length} expirations
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
