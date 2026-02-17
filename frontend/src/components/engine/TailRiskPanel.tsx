import { useEngineTailRisk } from "../../hooks/useEngine"

export default function TailRiskPanel() {
  const { data: assessment, isLoading } = useEngineTailRisk()

  if (isLoading) {
    return (
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <div className="text-zinc-500 text-sm">Loading tail risk data...</div>
      </div>
    )
  }

  if (!assessment) return null

  return (
    <div className="space-y-4">
      {/* Tail Risk Intro */}
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-1">
          Tail Risk Framework
        </h3>
        <p className="text-zinc-600 text-[10px] leading-relaxed">
          This panel monitors three layers of portfolio protection.{" "}
          <span className="text-zinc-500">Early Warnings</span> are leading indicators (credit spreads, bid-ask, correlation, VVIX)
          that fire 2-4 weeks before equity vol spikes.{" "}
          <span className="text-zinc-500">Hedge Allocation</span> shows the standing 2% annual budget split across
          VIX call spreads, SPX put spreads, and scheduled OTM puts.{" "}
          <span className="text-zinc-500">3-Pillar Tail Trading</span> activates when the 1M-3M term structure inverts
          (fewer than 80 occurrences since 2004) -- signaling a rare opportunity to trade the recovery.
          Crisis protocol triggers automatically when VIX &gt; 35 or 3+ warnings fire simultaneously.
        </p>
      </div>

      {/* Crisis Protocol */}
      {assessment.crisis_protocol_active && (
        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
          <div className="text-red-400 font-bold text-sm mb-2">
            CRISIS PROTOCOL ACTIVE
          </div>
          <div className="space-y-1">
            {assessment.crisis_actions.map((action, i) => (
              <div key={i} className="text-red-300 text-xs">
                {action}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Early Warning Signals */}
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider">
            Early Warning Signals
          </h3>
          <span className={`text-xs font-medium ${
            assessment.active_warnings_count > 0 ? "text-orange-400" : "text-green-400"
          }`}>
            {assessment.active_warnings_count} Active
          </span>
        </div>

        <div className="space-y-2">
          {assessment.early_warnings.map((warning, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 p-2 rounded ${
                warning.triggered
                  ? "bg-red-500/10 border border-red-500/20"
                  : "bg-zinc-800/30"
              }`}
            >
              {/* Traffic light */}
              <div className={`w-2 h-2 rounded-full mt-1.5 ${
                warning.triggered ? "bg-red-500" : "bg-green-500"
              }`} />
              <div className="flex-1">
                <div className="text-zinc-300 text-xs font-medium">
                  {warning.signal}
                </div>
                <div className="text-zinc-500 text-[10px]">
                  Action: {warning.action}
                </div>
                {warning.current_value != null && (
                  <div className="text-zinc-500 text-[10px]">
                    Current: {warning.current_value.toFixed(1)} / Threshold: {warning.threshold?.toFixed(1)}
                  </div>
                )}
                {warning.lead_time && (
                  <div className="text-zinc-600 text-[10px]">
                    Lead time: {warning.lead_time}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Hedge Allocation */}
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-3">
          Hedge Allocation ({(assessment.hedge_allocation.annual_budget_pct * 100).toFixed(0)}% Annual Budget)
        </h3>

        <div className="space-y-2">
          {assessment.hedge_allocation.instruments.map((inst, i) => (
            <div key={i} className="bg-zinc-800/50 rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-zinc-200 text-xs font-medium">{inst.name}</span>
                <span className="text-blue-400 text-xs font-bold">
                  {(inst.allocation * 100).toFixed(0)}%
                </span>
              </div>
              {/* Allocation bar */}
              <div className="h-1.5 bg-zinc-700 rounded overflow-hidden mb-2">
                <div
                  className="h-full bg-blue-500 rounded"
                  style={{ width: `${inst.allocation * 100}%` }}
                />
              </div>
              <div className="text-zinc-500 text-[10px]">{inst.structure}</div>
              {inst.tenor && (
                <div className="text-zinc-600 text-[10px]">{inst.tenor}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 3-Pillar Tail Trading Signal */}
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
        <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-3">
          3-Pillar Tail Trading (JPM)
        </h3>

        <div className="flex items-center gap-3 mb-3">
          <span className={`text-sm font-bold ${
            assessment.tail_trading.signal_active ? "text-red-400" : "text-green-400"
          }`}>
            Signal: {assessment.tail_trading.signal_active ? "ACTIVE" : "Inactive"}
          </span>
          <span className="text-zinc-500 text-xs">
            TS 1M-3M: {assessment.tail_trading.ts_value.toFixed(2)}
            {assessment.tail_trading.ts_value < 0 ? " (INVERTED)" : " (contango)"}
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2">
          {[
            { name: "Delta Pillar", active: assessment.tail_trading.delta_pillar_active, desc: "Spot recovery" },
            { name: "Gamma Pillar", active: assessment.tail_trading.gamma_pillar_active, desc: "Realized vol" },
            { name: "Vega Pillar", active: assessment.tail_trading.vega_pillar_active, desc: "VIX normalization" },
          ].map((pillar) => (
            <div
              key={pillar.name}
              className={`p-2 rounded border text-center ${
                pillar.active
                  ? "bg-red-500/10 border-red-500/30 text-red-400"
                  : "bg-zinc-800/30 border-zinc-700 text-zinc-500"
              }`}
            >
              <div className="text-xs font-medium">{pillar.name}</div>
              <div className="text-[10px]">{pillar.desc}</div>
              <div className="text-[10px] font-bold mt-1">
                {pillar.active ? "ON" : "OFF"}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
