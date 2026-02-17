import { useState, useMemo } from "react"
import { RefreshCw } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select } from "@/components/ui/select"
import { useOptionChain } from "@/hooks/useMarketData"
import { formatPrice, formatPercent, formatVolume, formatGreek } from "@/lib/utils"
import type { Market } from "@/lib/api"

interface OptionsChainProps {
  symbol: string
  market: Market
}

export function OptionsChain({ symbol, market }: OptionsChainProps) {
  const [selectedExpiration, setSelectedExpiration] = useState<string>("")

  const { data: chain, isLoading, isError } = useOptionChain(
    symbol,
    market,
    selectedExpiration || undefined,
    !!symbol
  )

  // Set default expiration when chain loads
  useMemo(() => {
    if (chain?.expirations?.length && !selectedExpiration) {
      setSelectedExpiration(chain.expirations[0])
    }
  }, [chain?.expirations, selectedExpiration])

  // Filter options by selected expiration
  const filteredCalls = useMemo(() => {
    if (!chain || !selectedExpiration) return []
    return chain.calls.filter((c) => c.expiration === selectedExpiration)
  }, [chain, selectedExpiration])

  const filteredPuts = useMemo(() => {
    if (!chain || !selectedExpiration) return []
    return chain.puts.filter((p) => p.expiration === selectedExpiration)
  }, [chain, selectedExpiration])

  // Group by strike
  const strikes = useMemo(() => {
    const allStrikes = new Set([
      ...filteredCalls.map((c) => c.strike),
      ...filteredPuts.map((p) => p.strike),
    ])
    return Array.from(allStrikes).sort((a, b) => a - b)
  }, [filteredCalls, filteredPuts])

  const getCurrencyForMarket = (m: Market) => {
    const currencies: Record<Market, string> = { US: "USD", JP: "JPY", HK: "HKD" }
    return currencies[m]
  }

  if (!symbol) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Options Chain</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8 text-xs">
            Enter a symbol to view options chain
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div className="flex items-center gap-3">
          <CardTitle>{symbol}</CardTitle>
          <span className="text-xs text-muted-foreground">OPTIONS CHAIN</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground uppercase">Expiry:</span>
          {chain?.expirations && (
            <Select
              value={selectedExpiration}
              onChange={(e) => setSelectedExpiration(e.target.value)}
              className="w-32"
            >
              {chain.expirations.map((exp) => (
                <option key={exp} value={exp}>
                  {exp}
                </option>
              ))}
            </Select>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="h-4 w-4 animate-spin text-primary" />
            <span className="ml-2 text-xs text-muted-foreground">Loading chain...</span>
          </div>
        )}

        {isError && (
          <div className="text-center py-8 text-destructive text-xs">
            Failed to fetch options chain
          </div>
        )}

        {chain && !isLoading && (
          <div className="overflow-x-auto">
            <table className="w-full bb-grid">
              <thead>
                <tr>
                  <th colSpan={5} className="text-center py-1.5 bg-bb-green/10 text-bb-green border-b border-border">
                    CALLS
                  </th>
                  <th className="py-1.5 bg-muted border-b border-border text-primary">STRIKE</th>
                  <th colSpan={5} className="text-center py-1.5 bg-bb-red/10 text-bb-red border-b border-border">
                    PUTS
                  </th>
                </tr>
                <tr>
                  <th>BID</th>
                  <th>ASK</th>
                  <th>VOL</th>
                  <th>IV</th>
                  <th>DELTA</th>
                  <th className="bg-muted text-primary"></th>
                  <th>DELTA</th>
                  <th>IV</th>
                  <th>VOL</th>
                  <th>BID</th>
                  <th>ASK</th>
                </tr>
              </thead>
              <tbody>
                {strikes.map((strike) => {
                  const call = filteredCalls.find((c) => c.strike === strike)
                  const put = filteredPuts.find((p) => p.strike === strike)
                  const isATM = chain.underlying_price && Math.abs(strike - chain.underlying_price) < (chain.underlying_price * 0.01)

                  return (
                    <tr key={strike} className={isATM ? "bg-primary/10" : ""}>
                      <td className="text-bb-green">
                        {formatPrice(call?.bid, getCurrencyForMarket(market))}
                      </td>
                      <td className="text-bb-green">
                        {formatPrice(call?.ask, getCurrencyForMarket(market))}
                      </td>
                      <td>{formatVolume(call?.volume)}</td>
                      <td className="text-bb-amber">
                        {formatPercent(call?.implied_volatility)}
                      </td>
                      <td className="text-bb-cyan">
                        {formatGreek(call?.greeks?.delta)}
                      </td>
                      <td className="text-center font-semibold bg-muted text-primary">
                        {formatPrice(strike, getCurrencyForMarket(market))}
                      </td>
                      <td className="text-bb-cyan">
                        {formatGreek(put?.greeks?.delta)}
                      </td>
                      <td className="text-bb-amber">
                        {formatPercent(put?.implied_volatility)}
                      </td>
                      <td>{formatVolume(put?.volume)}</td>
                      <td className="text-bb-red">
                        {formatPrice(put?.bid, getCurrencyForMarket(market))}
                      </td>
                      <td className="text-bb-red">
                        {formatPrice(put?.ask, getCurrencyForMarket(market))}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {strikes.length === 0 && (
              <p className="text-center py-4 text-muted-foreground text-xs">
                No options available for this expiration
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
