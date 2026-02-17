import { useMarketIndicators } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Market, SectorData } from "@/lib/api"

interface SectorHeatmapProps {
  className?: string
  onSectorSelect?: (symbol: string, market: Market) => void
}

function getHeatmapColor(changePercent: number | null): string {
  if (changePercent === null) return "bg-muted"

  const absChange = Math.abs(changePercent)

  if (changePercent >= 0) {
    if (absChange < 0.5) return "bg-bb-green/20"
    if (absChange < 1) return "bg-bb-green/40"
    if (absChange < 2) return "bg-bb-green/60"
    return "bg-bb-green/80"
  } else {
    if (absChange < 0.5) return "bg-bb-red/20"
    if (absChange < 1) return "bg-bb-red/40"
    if (absChange < 2) return "bg-bb-red/60"
    return "bg-bb-red/80"
  }
}

function getTextColor(changePercent: number | null): string {
  if (changePercent === null) return "text-muted-foreground"
  return changePercent >= 0 ? "text-bb-green" : "text-bb-red"
}

interface SectorTileProps {
  sector: SectorData
  onClick?: () => void
}

function SectorTile({ sector, onClick }: SectorTileProps) {
  const bgColor = getHeatmapColor(sector.change_percent)
  const textColor = getTextColor(sector.change_percent)

  return (
    <button
      onClick={onClick}
      className={cn(
        "p-1.5 rounded transition-all hover:ring-1 hover:ring-primary/50",
        "flex flex-col items-center justify-center text-center",
        bgColor
      )}
    >
      <span className="text-[10px] font-semibold text-foreground">{sector.symbol}</span>
      <span className={cn("text-[9px] font-bold tabular-nums", textColor)}>
        {sector.change_percent !== null
          ? `${sector.change_percent >= 0 ? "+" : ""}${sector.change_percent.toFixed(1)}%`
          : "N/A"}
      </span>
    </button>
  )
}

export function SectorHeatmap({ className, onSectorSelect }: SectorHeatmapProps) {
  const { data, isLoading } = useMarketIndicators()

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">SECTORS</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const sectors = data?.sectors
  if (!sectors || sectors.length === 0) return null

  // Sort by change percent for visual interest
  const sortedSectors = [...sectors].sort((a, b) => {
    const aChange = a.change_percent ?? 0
    const bChange = b.change_percent ?? 0
    return bChange - aChange
  })

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center justify-between">
          <span>SECTORS</span>
          <span className="text-[10px] text-muted-foreground font-normal">S&P 500</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-1">
          {sortedSectors.map((sector) => (
            <SectorTile
              key={sector.symbol}
              sector={sector}
              onClick={() => onSectorSelect?.(sector.symbol, "US")}
            />
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 mt-2 text-[9px] text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-3 h-2 rounded bg-bb-red/80" />
            <span>-2%+</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-2 rounded bg-muted" />
            <span>0%</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-2 rounded bg-bb-green/80" />
            <span>+2%+</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
