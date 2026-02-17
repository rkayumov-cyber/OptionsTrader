import { useState } from "react"
import { useEngineRecommendations } from "../../hooks/useEngine"
import type { StrategyCandidate, StrategyScore } from "../../lib/engineApi"

const OBJECTIVES = [
  { value: "income", label: "Income" },
  { value: "directional", label: "Directional" },
  { value: "hedging", label: "Hedging" },
  { value: "event", label: "Event" },
  { value: "relative_value", label: "Relative Value" },
  { value: "tail", label: "Tail Trading" },
  { value: "all", label: "All" },
]

const REC_COLORS: Record<string, string> = {
  TRADE: "text-green-400",
  TRADE_CAUTIOUS: "text-yellow-400",
  LOW_CONVICTION: "text-orange-400",
  NO_TRADE: "text-red-400",
  REGIME_UNCERTAIN: "text-zinc-400",
}

function ScoreBar({ label, value, max = 10 }: { label: string; value: number; max?: number }) {
  const pct = (value / max) * 100
  const color =
    pct >= 70 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500"
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-zinc-500 w-20 text-right">{label}</span>
      <div className="flex-1 h-1.5 bg-zinc-800 rounded overflow-hidden">
        <div className={`h-full ${color} rounded`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-zinc-400 w-8">{value.toFixed(1)}</span>
    </div>
  )
}

function StrategyCard({ candidate, rank }: { candidate: StrategyCandidate; rank: number }) {
  const { scores, params, template } = candidate
  return (
    <div className="bg-zinc-800/50 border border-zinc-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-zinc-500 text-xs font-bold">#{rank}</span>
          <span className="text-zinc-200 font-medium text-sm">
            {candidate.name.replace(/_/g, " ")}
          </span>
          <span className="text-zinc-500 text-xs px-1.5 py-0.5 bg-zinc-800 rounded">
            {template.family}
          </span>
        </div>
        <span className="text-lg font-bold text-green-400">
          {scores.total.toFixed(1)}
        </span>
      </div>

      <p className="text-zinc-400 text-xs mb-3">{template.description}</p>

      {/* 6-Dimension Scores */}
      <div className="space-y-1 mb-3">
        <ScoreBar label="Edge" value={scores.edge} />
        <ScoreBar label="Carry Fit" value={scores.carry_fit} />
        <ScoreBar label="Tail Risk" value={scores.tail_risk} />
        <ScoreBar label="Robust" value={scores.robustness} />
        <ScoreBar label="Liquidity" value={scores.liquidity} />
        <ScoreBar label="Simple" value={scores.complexity} />
      </div>

      {/* Parameters */}
      <div className="grid grid-cols-3 gap-2 text-xs">
        {params.delta != null && (
          <div className="bg-zinc-900/50 rounded p-2">
            <div className="text-zinc-500">Delta</div>
            <div className="text-zinc-200 font-medium">{params.delta}</div>
          </div>
        )}
        {params.deltas && (
          <div className="bg-zinc-900/50 rounded p-2 col-span-2">
            <div className="text-zinc-500">Deltas</div>
            <div className="text-zinc-200 font-medium">
              {Object.entries(params.deltas).map(([k, v]) => `${k}:${v}`).join(" / ")}
            </div>
          </div>
        )}
        <div className="bg-zinc-900/50 rounded p-2">
          <div className="text-zinc-500">DTE</div>
          <div className="text-zinc-200 font-medium">{params.dte}</div>
        </div>
        <div className="bg-zinc-900/50 rounded p-2">
          <div className="text-zinc-500">Size Mult</div>
          <div className="text-zinc-200 font-medium">{params.size_multiplier}x</div>
        </div>
        <div className="bg-zinc-900/50 rounded p-2">
          <div className="text-zinc-500">Target</div>
          <div className="text-zinc-200 font-medium">
            {typeof params.profit_target === "number"
              ? `${(params.profit_target * 100).toFixed(0)}%`
              : params.profit_target}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function StrategyRecommendations() {
  const [nav, setNav] = useState(100_000)
  const [objective, setObjective] = useState("income")
  const { data: rec, isLoading } = useEngineRecommendations(nav, objective)

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-1">
        <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider">
          Strategy Recommendations
        </h3>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={nav}
            onChange={(e) => setNav(Number(e.target.value))}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300 w-28"
            placeholder="NAV"
          />
          <select
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
          >
            {OBJECTIVES.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
      </div>
      <p className="text-zinc-600 text-[10px] mb-3 leading-relaxed">
        Enter your portfolio value and choose an objective. The engine filters 19 strategy templates through
        7 gates (IV rank, event avoidance, liquidity, regime compatibility, etc.) then scores the survivors
        on edge, carry fit, tail risk, robustness, liquidity, and complexity. Top 3 are shown with
        regime-adjusted parameters. Scores above 7 are strong; below 5 is low conviction.
      </p>

      {isLoading ? (
        <div className="text-zinc-500 text-sm">Analyzing strategies...</div>
      ) : rec ? (
        <div className="space-y-3">
          {/* Recommendation Status */}
          <div className="flex items-center gap-2">
            <span className={`font-bold text-sm ${REC_COLORS[rec.recommendation] || "text-zinc-400"}`}>
              {rec.recommendation.replace("_", " ")}
            </span>
            {rec.note && (
              <span className="text-zinc-500 text-xs">{rec.note}</span>
            )}
          </div>

          {/* Strategy Cards */}
          {rec.strategies.map((candidate, i) => (
            <StrategyCard key={candidate.name} candidate={candidate} rank={i + 1} />
          ))}

          {rec.strategies.length === 0 && (
            <div className="text-zinc-500 text-sm py-4 text-center">
              No strategies match current conditions for this objective
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
