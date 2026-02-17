import { useState } from "react"
import { useEvaluatePosition } from "../../hooks/useEngine"
import type { RuleEvaluation, RulePriority } from "../../lib/engineApi"

const PRIORITY_COLORS: Record<RulePriority, string> = {
  CRITICAL: "bg-red-500/20 text-red-400 border-red-500/30",
  HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  MEDIUM: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  LOW: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30",
}

function RuleRow({ rule }: { rule: RuleEvaluation }) {
  return (
    <div className={`border rounded p-2 ${PRIORITY_COLORS[rule.priority]}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="font-medium text-xs">
          {rule.rule_id}: {rule.rule_name}
        </span>
        <span className="text-[10px] uppercase font-bold">{rule.priority}</span>
      </div>
      <div className="text-xs opacity-80">{rule.action}</div>
      {rule.details && (
        <div className="text-[10px] opacity-60 mt-1">{rule.details}</div>
      )}
    </div>
  )
}

export default function PositionHealthCheck() {
  const [form, setForm] = useState({
    dte: 30,
    strategy: "cash_secured_put",
    family: "short_premium",
    current_delta: 15,
    initial_delta: 12,
    unrealized_pnl: 50,
    max_profit: 200,
    premium_received: 200,
    premium_paid: 0,
  })

  const mutation = useEvaluatePosition()

  const handleEvaluate = () => {
    mutation.mutate(form)
  }

  const health = mutation.data

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
      <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-4">
        Position Health Check
      </h3>

      {/* Input Form */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <div>
          <label className="text-zinc-500 text-[10px] block mb-1">Strategy</label>
          <select
            value={form.strategy}
            onChange={(e) => setForm({ ...form, strategy: e.target.value })}
            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
          >
            <option value="cash_secured_put">Cash Secured Put</option>
            <option value="put_credit_spread">Put Credit Spread</option>
            <option value="iron_condor">Iron Condor</option>
            <option value="short_strangle">Short Strangle</option>
            <option value="covered_call">Covered Call</option>
            <option value="call_debit_spread">Call Debit Spread</option>
            <option value="put_debit_spread">Put Debit Spread</option>
          </select>
        </div>
        <div>
          <label className="text-zinc-500 text-[10px] block mb-1">DTE</label>
          <input
            type="number"
            value={form.dte}
            onChange={(e) => setForm({ ...form, dte: Number(e.target.value) })}
            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
          />
        </div>
        <div>
          <label className="text-zinc-500 text-[10px] block mb-1">Family</label>
          <select
            value={form.family}
            onChange={(e) => setForm({ ...form, family: e.target.value })}
            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
          >
            <option value="short_premium">Short Premium</option>
            <option value="long_premium">Long Premium</option>
          </select>
        </div>
        <div>
          <label className="text-zinc-500 text-[10px] block mb-1">P&L</label>
          <input
            type="number"
            value={form.unrealized_pnl}
            onChange={(e) => setForm({ ...form, unrealized_pnl: Number(e.target.value) })}
            className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs text-zinc-300"
          />
        </div>
      </div>

      <button
        onClick={handleEvaluate}
        disabled={mutation.isPending}
        className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium py-2 rounded mb-4 disabled:opacity-50"
      >
        {mutation.isPending ? "Evaluating..." : "Evaluate Position"}
      </button>

      {/* Results */}
      {health && (
        <div className="space-y-3">
          {/* Summary */}
          <div className="flex items-center gap-3">
            <span className="text-zinc-200 text-sm font-medium">
              {health.triggered_count === 0
                ? "Position Healthy"
                : `${health.triggered_count} Rule(s) Triggered`}
            </span>
            {health.critical_count > 0 && (
              <span className="text-red-400 text-xs px-2 py-0.5 bg-red-500/10 rounded">
                {health.critical_count} CRITICAL
              </span>
            )}
          </div>

          {/* Recommended Action */}
          <div className="text-sm text-zinc-300 p-2 bg-zinc-800/50 rounded border border-zinc-700">
            {health.recommended_action}
          </div>

          {/* Adjustment Rules */}
          {health.adjustment_rules.length > 0 && (
            <div>
              <div className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">
                Adjustment Rules (A1-A9)
              </div>
              <div className="space-y-1">
                {health.adjustment_rules.map((rule) => (
                  <RuleRow key={rule.rule_id} rule={rule} />
                ))}
              </div>
            </div>
          )}

          {/* Exit Rules */}
          {health.exit_rules.length > 0 && (
            <div>
              <div className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">
                Exit Rules (X1-X7)
              </div>
              <div className="space-y-1">
                {health.exit_rules.map((rule) => (
                  <RuleRow key={rule.rule_id} rule={rule} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
