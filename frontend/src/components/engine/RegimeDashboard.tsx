import { useEngineRegime } from "../../hooks/useEngine"
import type { VolRegime, Trend, Confidence, EventType } from "../../lib/engineApi"

const REGIME_COLORS: Record<VolRegime, string> = {
  VERY_LOW: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  LOW: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  NORMAL: "bg-green-500/20 text-green-400 border-green-500/30",
  ELEVATED: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  EXTREME: "bg-red-500/20 text-red-400 border-red-500/30",
  CRISIS: "bg-red-600/30 text-red-300 border-red-600/50",
  LIQUIDITY_STRESS: "bg-purple-500/20 text-purple-400 border-purple-500/30",
}

const TREND_ARROWS: Record<Trend, string> = {
  STRONG_UPTREND: "^^ Strong Up",
  UPTREND: "^ Up",
  RANGE_BOUND: "~ Range",
  DOWNTREND: "v Down",
  STRONG_DOWNTREND: "vv Strong Down",
}

const CONFIDENCE_COLORS: Record<Confidence, string> = {
  HIGH: "text-green-400",
  MEDIUM: "text-yellow-400",
  LOW: "text-red-400",
}

export default function RegimeDashboard() {
  const { data: regime, isLoading, error } = useEngineRegime()

  if (isLoading) {
    return (
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <div className="text-zinc-500 text-sm">Loading regime data...</div>
      </div>
    )
  }

  if (error || !regime) {
    return (
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <div className="text-red-400 text-sm">Failed to load regime data</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Regime Header */}
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider">
            Market Regime
          </h3>
          <span className="text-zinc-500 text-xs">
            {new Date(regime.timestamp).toLocaleTimeString()}
          </span>
        </div>

        <div className="flex items-center gap-4 mb-4">
          {/* Regime Badge */}
          <span
            className={`px-3 py-1.5 rounded border text-sm font-bold ${REGIME_COLORS[regime.regime]}`}
          >
            {regime.regime.replace("_", " ")}
          </span>

          {/* Trend */}
          <span className="text-zinc-300 text-sm">
            {TREND_ARROWS[regime.trend]}
          </span>

          {/* Confidence */}
          <span className={`text-sm ${CONFIDENCE_COLORS[regime.confidence]}`}>
            {regime.confidence} confidence ({regime.confirming_signals}/4)
          </span>

          {/* VVIX Warning */}
          {regime.vol_unstable && (
            <span className="text-orange-400 text-xs px-2 py-0.5 bg-orange-500/10 rounded">
              VVIX Unstable
            </span>
          )}
        </div>

        {/* Event State */}
        {regime.event_active && (
          <div className="mb-3 p-2 bg-amber-500/10 border border-amber-500/20 rounded text-sm">
            <span className="text-amber-400 font-medium">
              Event Window: {regime.event_type}
            </span>
            {regime.multi_event && (
              <span className="ml-2 text-amber-300 text-xs">
                (Multi-event week: +40% IV premium)
              </span>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="space-y-1">
          <div className="text-zinc-500 text-xs font-medium uppercase tracking-wider mb-1">
            Recommended Actions
          </div>
          {regime.actions.map((action, i) => (
            <div key={i} className="text-zinc-300 text-sm pl-2 border-l border-zinc-700">
              {action}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
