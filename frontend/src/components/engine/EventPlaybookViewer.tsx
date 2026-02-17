import { useState } from "react"
import { useEnginePlaybook, useEngineZeroDTE } from "../../hooks/useEngine"

const EVENT_TYPES = ["FOMC", "EARNINGS", "CPI", "NFP"]
const PHASE_COLORS: Record<string, string> = {
  pre_event: "border-blue-500/30 bg-blue-500/5",
  event_eve: "border-yellow-500/30 bg-yellow-500/5",
  post_event: "border-green-500/30 bg-green-500/5",
}

const DAY_BIAS_COLORS: Record<string, string> = {
  SELL: "text-green-400",
  "SELL straddles at 10am": "text-green-400",
  "SELL if no weekend event risk": "text-green-400",
  "AVOID or buy premium": "text-red-400",
  "AVOID/BUY": "text-red-400",
  "Selective selling only": "text-yellow-400",
  SELECTIVE: "text-yellow-400",
}

export default function EventPlaybookViewer() {
  const [eventType, setEventType] = useState("FOMC")
  const [show0DTE, setShow0DTE] = useState(false)
  const { data: playbook, isLoading } = useEnginePlaybook(show0DTE ? "" : eventType)
  const { data: zeroDte } = useEngineZeroDTE()

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider">
          Event Playbooks
        </h3>
        <div className="flex items-center gap-2">
          {EVENT_TYPES.map((et) => (
            <button
              key={et}
              onClick={() => { setEventType(et); setShow0DTE(false); }}
              className={`px-2 py-1 rounded text-xs ${
                !show0DTE && eventType === et
                  ? "bg-blue-600 text-white"
                  : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {et}
            </button>
          ))}
          <button
            onClick={() => setShow0DTE(true)}
            className={`px-2 py-1 rounded text-xs ${
              show0DTE
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            0DTE
          </button>
        </div>
      </div>

      {/* Event Playbook */}
      {!show0DTE && (
        isLoading ? (
          <div className="text-zinc-500 text-sm">Loading playbook...</div>
        ) : playbook ? (
          <div className="space-y-3">
            {/* Timeline Phases */}
            {playbook.phases.map((phase) => (
              <div
                key={phase.phase}
                className={`border rounded-lg p-3 ${PHASE_COLORS[phase.phase] || "border-zinc-700"}`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-zinc-200 text-xs font-bold uppercase">
                    {phase.phase.replace("_", " ")}
                  </span>
                  <span className="text-zinc-500 text-[10px]">{phase.timing}</span>
                </div>
                {phase.iv_behavior && (
                  <div className="text-zinc-400 text-xs mb-1">
                    <span className="text-zinc-500">IV: </span>{phase.iv_behavior}
                  </div>
                )}
                <div className="text-zinc-300 text-xs mb-1">
                  <span className="text-zinc-500">Strategy: </span>{phase.strategy}
                </div>
                <div className="text-zinc-400 text-xs">
                  <span className="text-zinc-500">Sizing: </span>{phase.sizing}
                </div>
              </div>
            ))}

            {/* Notes */}
            {playbook.notes.length > 0 && (
              <div className="mt-3">
                <div className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Notes</div>
                {playbook.notes.map((note, i) => (
                  <div key={i} className="text-zinc-400 text-xs pl-2 border-l border-zinc-700 mb-1">
                    {note}
                  </div>
                ))}
              </div>
            )}

            {/* Key Rules (Earnings) */}
            {playbook.key_rules.length > 0 && (
              <div className="mt-3">
                <div className="text-zinc-500 text-[10px] uppercase tracking-wider mb-1">Key Rules</div>
                {playbook.key_rules.map((rule, i) => (
                  <div key={i} className="text-zinc-400 text-xs pl-2 border-l border-amber-500/30 mb-1">
                    {rule}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : null
      )}

      {/* 0DTE Playbook */}
      {show0DTE && zeroDte && (
        <div className="space-y-3">
          {/* Day-of-Week Grid */}
          <div className="space-y-2">
            {zeroDte.days.map((day) => (
              <div key={day.day} className="flex items-center gap-3 bg-zinc-800/50 rounded p-2">
                <span className="text-zinc-200 text-xs font-medium w-20">{day.day}</span>
                <span className="text-zinc-400 text-xs w-24">{day.premium}</span>
                <span className={`text-xs flex-1 ${DAY_BIAS_COLORS[day.bias] || "text-zinc-400"}`}>
                  {day.bias}
                </span>
                <span className="text-zinc-500 text-[10px] w-28 text-right">
                  {day.gamma_imbalance}
                </span>
              </div>
            ))}
          </div>

          {/* Characteristics */}
          <div className="text-zinc-500 text-[10px] space-y-1 mt-2">
            <div>Entry: {zeroDte.entry_rule}</div>
            <div>Block: {zeroDte.event_block}</div>
            {Object.entries(zeroDte.characteristics).map(([k, v]) => (
              <div key={k}>{k}: {String(v)}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
