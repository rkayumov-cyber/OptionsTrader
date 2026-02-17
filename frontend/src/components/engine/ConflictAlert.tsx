import { useEngineConflicts } from "../../hooks/useEngine"

export default function ConflictAlert() {
  const { data: conflicts } = useEngineConflicts()

  if (!conflicts) return null

  const detected = conflicts.filter((c) => c.detected)
  if (detected.length === 0) return null

  return (
    <div className="bg-amber-900/10 border border-amber-500/20 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-amber-400 text-xs font-bold uppercase">
          Signal Conflicts Detected ({detected.length})
        </span>
      </div>
      <div className="space-y-2">
        {detected.map((conflict) => (
          <div
            key={conflict.conflict_id}
            className="bg-zinc-900/50 rounded p-2 border border-amber-500/10"
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-amber-400 text-xs font-medium">
                {conflict.conflict_id}:
              </span>
              <span className="text-zinc-300 text-xs">{conflict.description}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-[10px] mb-1">
              <div className="text-zinc-500">
                <span className="text-zinc-600">A: </span>{conflict.signal_a}
              </div>
              <div className="text-zinc-500">
                <span className="text-zinc-600">B: </span>{conflict.signal_b}
              </div>
            </div>
            <div className="text-amber-300/80 text-xs">
              {conflict.resolution}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
