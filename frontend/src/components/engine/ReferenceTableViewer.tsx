import { useState } from "react"
import { useEngineReferenceTable, useEngineReferenceTables } from "../../hooks/useEngine"

const TABLE_LABELS: Record<string, string> = {
  put_selling: "Put Selling by Delta (GS 10yr)",
  overwriting: "Overwriting by FCF Quintile (GS 16yr)",
  hedging: "Hedging Strategy Comparison (GS 27yr)",
  sector_sensitivity: "Sector Event Sensitivity (GS 15yr)",
  global_vol: "Global Vol Levels (JPM)",
  zero_dte_premium: "0DTE Day-of-Week Premium (JPM)",
  vol_risk_premium: "Vol Risk Premium Matrix (JPM)",
  tail_trading: "3-Pillar Tail Performance (JPM)",
}

export default function ReferenceTableViewer() {
  const { data: tables } = useEngineReferenceTables()
  const [selected, setSelected] = useState("put_selling")
  const { data: tableData, isLoading } = useEngineReferenceTable(selected)

  const tableNames = tables?.tables || Object.keys(TABLE_LABELS)

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
      <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-3">
        Reference Tables (GS/JPM Research)
      </h3>

      {/* Tab buttons */}
      <div className="flex flex-wrap gap-1 mb-4">
        {tableNames.map((name) => (
          <button
            key={name}
            onClick={() => setSelected(name)}
            className={`px-2 py-1 rounded text-[10px] ${
              selected === name
                ? "bg-blue-600 text-white"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            {TABLE_LABELS[name] || name}
          </button>
        ))}
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-zinc-500 text-sm">Loading table...</div>
      ) : tableData && tableData.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-zinc-700">
                {Object.keys(tableData[0]).map((col) => (
                  <th
                    key={col}
                    className="text-zinc-500 text-left py-2 px-2 font-medium uppercase tracking-wider text-[10px]"
                  >
                    {col.replace(/_/g, " ")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, i) => (
                <tr key={i} className="border-b border-zinc-800 hover:bg-zinc-800/50">
                  {Object.values(row).map((val, j) => (
                    <td key={j} className="py-1.5 px-2 text-zinc-300">
                      {typeof val === "number"
                        ? val % 1 === 0
                          ? val
                          : val.toFixed(2)
                        : val == null
                        ? "-"
                        : String(val)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-zinc-500 text-sm">No data available</div>
      )}
    </div>
  )
}
