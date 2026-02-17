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

const TABLE_DESCRIPTIONS: Record<string, string> = {
  put_selling: "GS 10-year study: systematic put selling performance by delta (10-50). Shows annual return, Sharpe ratio, win rate, and max drawdown. The 10-15 delta range has the best risk-adjusted returns.",
  overwriting: "GS 16-year covered call study: stocks sorted by free cash flow yield quintile. Q5 (highest FCF) delivered 8.8% annual premium with Sharpe 0.76 -- stock selection matters more than strike selection.",
  hedging: "GS 27-year comparison of hedging instruments: SPX puts, VIX calls, put spreads, collars, tail risk funds. VIX calls offer 3-5x convexity vs SPX puts in true crises; scheduled buying outperforms discretionary.",
  sector_sensitivity: "GS 15-year sector analysis: how each sector's IV responds to a 5-point VIX spike. Technology and Consumer Discretionary are most sensitive; Utilities and Staples are most defensive.",
  global_vol: "JPM cross-market implied volatility levels across US (VIX), Europe (V2X), Japan (VNKY), and EM indices. Useful for relative value and identifying cheap convexity globally.",
  zero_dte_premium: "JPM study of 0DTE options vol premium by day of week. Thursday has the highest premium (1.5x), Monday the lowest (0.3x). Use this to time short-dated premium selling.",
  vol_risk_premium: "GS/JPM combined data on the volatility risk premium (implied minus realized vol) across different VIX regimes. The premium is largest at VIX 20-25 and compresses in crisis.",
  tail_trading: "JPM 3-pillar tail trading backtest: delta pillar (spot recovery call spreads), gamma pillar (5D 25-delta calls, 62.2% hit rate), vega pillar (VIX put ladders). Signal: term structure inversion.",
}

export default function ReferenceTableViewer() {
  const { data: tables } = useEngineReferenceTables()
  const [selected, setSelected] = useState("put_selling")
  const { data: tableData, isLoading } = useEngineReferenceTable(selected)

  const tableNames = tables?.tables || Object.keys(TABLE_LABELS)

  return (
    <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-4">
      <h3 className="text-zinc-400 text-xs font-medium uppercase tracking-wider mb-1">
        Reference Tables (GS/JPM Research)
      </h3>
      <p className="text-zinc-600 text-[10px] mb-3 leading-relaxed">
        Backtested performance data from Goldman Sachs (2003-2025) and JPMorgan derivatives research.
        Use these to set realistic return expectations, compare strategy performance across regimes,
        and validate the engine's recommendations against historical evidence.
      </p>

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

      {/* Selected Table Description */}
      {TABLE_DESCRIPTIONS[selected] && (
        <p className="text-zinc-500 text-[10px] mb-3 leading-relaxed px-1">
          {TABLE_DESCRIPTIONS[selected]}
        </p>
      )}

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
