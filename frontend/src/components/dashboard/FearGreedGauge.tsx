import { useQuery } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { getFearGreedIndex, type FearGreedResponse } from "@/lib/api"

interface FearGreedGaugeProps {
  className?: string
}

const getClassificationColor = (classification: string) => {
  switch (classification) {
    case "Extreme Fear":
      return "hsl(0 84% 60%)"
    case "Fear":
      return "hsl(24 100% 50%)"
    case "Neutral":
      return "hsl(38 92% 50%)"
    case "Greed":
      return "hsl(84 80% 44%)"
    case "Extreme Greed":
      return "hsl(142 76% 45%)"
    default:
      return "hsl(38 92% 50%)"
  }
}

const getScoreColor = (score: number) => {
  if (score < 25) return "hsl(0 84% 60%)"
  if (score < 45) return "hsl(24 100% 50%)"
  if (score < 55) return "hsl(38 92% 50%)"
  if (score < 75) return "hsl(84 80% 44%)"
  return "hsl(142 76% 45%)"
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

export function FearGreedGauge({ className }: FearGreedGaugeProps) {
  const { data, isLoading } = useQuery<FearGreedResponse>({
    queryKey: ["fear-greed"],
    queryFn: getFearGreedIndex,
    refetchInterval: 60000,
  })

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">FEAR & GREED INDEX</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-40">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const score = data?.score ?? 50
  const classification = data?.classification ?? "Neutral"
  const previousClose = data?.previous_close ?? 50
  const weekAgo = data?.week_ago ?? 50
  const components = data?.components ?? {}

  const mainColor = getClassificationColor(classification)

  // Gauge settings
  const cx = 100
  const cy = 70
  const radius = 55
  const strokeWidth = 8

  // Calculate needle angle (180 = left/fear, 0 = right/greed)
  const needleAngle = 180 - (score / 100) * 180
  const needleLength = radius - 10
  const needleEnd = polarToCartesian(cx, cy, needleLength, needleAngle)

  // Change indicators
  const dayChange = score - previousClose
  const weekChange = score - weekAgo

  return (
    <Card className={className}>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-1">
        <CardTitle className="text-sm">FEAR & GREED INDEX</CardTitle>
        <span
          className="text-xl font-bold tabular-nums"
          style={{ color: mainColor }}
        >
          {score.toFixed(0)}
        </span>
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        {/* Gauge */}
        <div className="flex flex-col items-center">
          <svg viewBox="0 0 200 85" className="w-full max-w-[170px]">
            {/* Background arc zones */}
            <path
              d={describeArc(cx, cy, radius, 0, 36)}
              fill="none"
              stroke="hsl(0 84% 60%)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 36, 72)}
              fill="none"
              stroke="hsl(24 100% 50%)"
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
              stroke="hsl(84 80% 44%)"
              strokeWidth={strokeWidth}
              opacity={0.2}
            />
            <path
              d={describeArc(cx, cy, radius, 144, 180)}
              fill="none"
              stroke="hsl(142 76% 45%)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.2}
            />

            {/* Active arc */}
            <path
              d={describeArc(cx, cy, radius, 0, 180 - needleAngle)}
              fill="none"
              stroke={mainColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />

            {/* Needle */}
            <line
              x1={cx}
              y1={cy}
              x2={needleEnd.x}
              y2={needleEnd.y}
              stroke={mainColor}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <circle cx={cx} cy={cy} r={4} fill={mainColor} />
            <circle cx={cx} cy={cy} r={1.5} fill="hsl(220 10% 4%)" />

            {/* Labels */}
            <text x="38" y="78" className="fill-muted-foreground" style={{ fontSize: '8px' }}>0</text>
            <text x="155" y="78" className="fill-muted-foreground" style={{ fontSize: '8px' }}>100</text>
          </svg>

          {/* Classification badge */}
          <div
            className="text-center px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider rounded"
            style={{ backgroundColor: `${mainColor}20`, color: mainColor }}
          >
            {classification}
          </div>

          <div className="flex justify-between w-full mt-1 text-[9px] text-muted-foreground uppercase">
            <span>Fear</span>
            <span>Greed</span>
          </div>
        </div>

        {/* Change indicators */}
        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div className="flex items-center justify-between px-2 py-1 bg-muted/30 rounded">
            <span className="text-muted-foreground">vs Yesterday</span>
            <span className={`flex items-center gap-0.5 font-medium ${dayChange > 0 ? 'text-bb-green' : dayChange < 0 ? 'text-bb-red' : 'text-muted-foreground'}`}>
              {dayChange > 0 ? <TrendingUp className="h-3 w-3" /> : dayChange < 0 ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
              {dayChange > 0 ? '+' : ''}{dayChange.toFixed(1)}
            </span>
          </div>
          <div className="flex items-center justify-between px-2 py-1 bg-muted/30 rounded">
            <span className="text-muted-foreground">vs Week Ago</span>
            <span className={`flex items-center gap-0.5 font-medium ${weekChange > 0 ? 'text-bb-green' : weekChange < 0 ? 'text-bb-red' : 'text-muted-foreground'}`}>
              {weekChange > 0 ? <TrendingUp className="h-3 w-3" /> : weekChange < 0 ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
              {weekChange > 0 ? '+' : ''}{weekChange.toFixed(1)}
            </span>
          </div>
        </div>

        {/* Component breakdown */}
        <div className="space-y-1">
          <div className="text-[9px] text-muted-foreground uppercase tracking-wide">Components</div>
          <div className="grid grid-cols-1 gap-0.5">
            {Object.entries(components).slice(0, 5).map(([key, comp]) => (
              <div key={key} className="flex items-center gap-2">
                <div className="flex-1 text-[9px] text-muted-foreground truncate">
                  {comp.name}
                </div>
                <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${comp.score}%`,
                      backgroundColor: getScoreColor(comp.score),
                    }}
                  />
                </div>
                <div
                  className="text-[9px] font-medium w-6 text-right tabular-nums"
                  style={{ color: getScoreColor(comp.score) }}
                >
                  {comp.score.toFixed(0)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
