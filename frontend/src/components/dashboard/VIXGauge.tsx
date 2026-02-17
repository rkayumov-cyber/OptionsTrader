import { useQuote } from "@/hooks/useMarketData"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2 } from "lucide-react"

interface VIXGaugeProps {
  className?: string
}

// VIX level zones with Bloomberg-style colors
const getVIXZone = (vix: number) => {
  if (vix < 15) return { label: "EXTREME GREED", color: "hsl(142 76% 45%)", zone: 0 }
  if (vix < 20) return { label: "GREED", color: "hsl(84 80% 44%)", zone: 1 }
  if (vix < 25) return { label: "NEUTRAL", color: "hsl(38 92% 50%)", zone: 2 }
  if (vix < 30) return { label: "FEAR", color: "hsl(24 100% 50%)", zone: 3 }
  return { label: "EXTREME FEAR", color: "hsl(0 84% 60%)", zone: 4 }
}

// SVG arc path generator
const describeArc = (
  x: number,
  y: number,
  radius: number,
  startAngle: number,
  endAngle: number
) => {
  const start = polarToCartesian(x, y, radius, endAngle)
  const end = polarToCartesian(x, y, radius, startAngle)
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1"
  return [
    "M", start.x, start.y,
    "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y,
  ].join(" ")
}

const polarToCartesian = (
  centerX: number,
  centerY: number,
  radius: number,
  angleInDegrees: number
) => {
  const angleInRadians = ((angleInDegrees - 180) * Math.PI) / 180
  return {
    x: centerX + radius * Math.cos(angleInRadians),
    y: centerY + radius * Math.sin(angleInRadians),
  }
}

export function VIXGauge({ className }: VIXGaugeProps) {
  const { data: quote, isLoading } = useQuote("VIX", "US")

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>VIX INDEX</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-32">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const vixValue = quote?.price || 20
  const zone = getVIXZone(vixValue)

  // Gauge settings
  const cx = 100
  const cy = 80
  const radius = 60
  const strokeWidth = 10

  // Calculate needle angle (180 = left, 0 = right)
  // VIX range: 10-50 mapped to 180-0 degrees
  const minVIX = 10
  const maxVIX = 50
  const clampedVIX = Math.max(minVIX, Math.min(maxVIX, vixValue))
  const needleAngle = 180 - ((clampedVIX - minVIX) / (maxVIX - minVIX)) * 180

  // Needle endpoint
  const needleLength = radius - 12
  const needleEnd = polarToCartesian(cx, cy, needleLength, needleAngle)

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle>VIX INDEX</CardTitle>
        <span className="text-xl font-bold tabular-nums" style={{ color: zone.color }}>
          {vixValue.toFixed(2)}
        </span>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-col items-center">
          <svg viewBox="0 0 200 95" className="w-full max-w-[180px]">
            {/* Background arc zones */}
            <path
              d={describeArc(cx, cy, radius, 0, 36)}
              fill="none"
              stroke="hsl(142 76% 45%)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 36, 72)}
              fill="none"
              stroke="hsl(84 80% 44%)"
              strokeWidth={strokeWidth}
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 72, 108)}
              fill="none"
              stroke="hsl(38 92% 50%)"
              strokeWidth={strokeWidth}
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 108, 144)}
              fill="none"
              stroke="hsl(24 100% 50%)"
              strokeWidth={strokeWidth}
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 144, 180)}
              fill="none"
              stroke="hsl(0 84% 60%)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.2}
            />

            {/* Active arc up to current value */}
            <path
              d={describeArc(cx, cy, radius, 0, 180 - needleAngle)}
              fill="none"
              stroke={zone.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Needle */}
            <line
              x1={cx}
              y1={cy}
              x2={needleEnd.x}
              y2={needleEnd.y}
              stroke={zone.color}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <circle cx={cx} cy={cy} r={5} fill={zone.color} />
            <circle cx={cx} cy={cy} r={2} fill="hsl(220 10% 4%)" />

            {/* Labels */}
            <text x="35" y="85" className="fill-muted-foreground" style={{ fontSize: '9px' }}>10</text>
            <text x="158" y="85" className="fill-muted-foreground" style={{ fontSize: '9px' }}>50</text>
          </svg>

          <div
            className="text-center px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider"
            style={{ backgroundColor: `${zone.color}20`, color: zone.color }}
          >
            {zone.label}
          </div>

          <div className="flex justify-between w-full mt-2 text-[10px] text-muted-foreground uppercase">
            <span>Greed</span>
            <span>Fear</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
