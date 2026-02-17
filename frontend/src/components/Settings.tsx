import { useState } from "react"
import { Settings as SettingsIcon, Check, Loader2, Server, Globe, Key } from "lucide-react"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useProviders, useSwitchProvider } from "@/hooks/useMarketData"
import { cn } from "@/lib/utils"

interface ProviderCardProps {
  name: string
  displayName: string
  description: string
  markets: string[]
  isActive: boolean
  onActivate: () => void
  isLoading: boolean
  children?: React.ReactNode
}

function ProviderCard({
  name,
  displayName,
  description,
  markets,
  isActive,
  onActivate,
  isLoading,
  children,
}: ProviderCardProps) {
  return (
    <Card className={cn(isActive && "ring-2 ring-primary")}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg">{displayName}</CardTitle>
            {isActive && (
              <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">
                Active
              </span>
            )}
          </div>
          {!isActive && (
            <Button size="sm" onClick={onActivate} disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Activate"
              )}
            </Button>
          )}
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex gap-1 mt-2">
          {markets.map((m) => (
            <span
              key={m}
              className="text-xs bg-muted px-2 py-0.5 rounded"
            >
              {m}
            </span>
          ))}
        </div>
      </CardHeader>
      {children && <CardContent className="pt-0">{children}</CardContent>}
    </Card>
  )
}

export function Settings() {
  const { data: providers } = useProviders()
  const switchProvider = useSwitchProvider()

  // IBKR settings
  const [ibkrHost, setIbkrHost] = useState("127.0.0.1")
  const [ibkrPort, setIbkrPort] = useState("7497")
  const [ibkrClientId, setIbkrClientId] = useState("1")

  // SAXO settings
  const [saxoToken, setSaxoToken] = useState("")
  const [saxoEnv, setSaxoEnv] = useState<"sim" | "live">("sim")

  const handleSwitchProvider = (
    provider: string,
    config?: {
      host?: string
      port?: number
      client_id?: number
      access_token?: string
      environment?: string
    }
  ) => {
    switchProvider.mutate({ provider, ...config })
  }

  const activeProvider = providers?.active || "mock"

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-4">
        <SettingsIcon className="h-5 w-5" />
        <h2 className="text-xl font-semibold">Provider Settings</h2>
      </div>

      <p className="text-sm text-muted-foreground mb-6">
        Configure your market data providers. Select a provider to activate it
        for fetching quotes, options chains, and volatility data.
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        {/* Mock Provider */}
        <ProviderCard
          name="mock"
          displayName="Mock Data"
          description="Simulated market data for testing and development. No external connection required."
          markets={["US", "JP", "HK"]}
          isActive={activeProvider === "mock"}
          onActivate={() => handleSwitchProvider("mock")}
          isLoading={switchProvider.isPending}
        />

        {/* Yahoo Provider */}
        <ProviderCard
          name="yahoo"
          displayName="Yahoo Finance"
          description="Free market data from Yahoo Finance. Real-time quotes with 15-min delay for some markets."
          markets={["US", "JP", "HK"]}
          isActive={activeProvider === "yahoo"}
          onActivate={() => handleSwitchProvider("yahoo")}
          isLoading={switchProvider.isPending}
        />

        {/* IBKR Provider */}
        <ProviderCard
          name="ibkr"
          displayName="Interactive Brokers"
          description="Professional-grade data via TWS or IB Gateway. Requires active IBKR account and running TWS/Gateway."
          markets={["US", "JP", "HK"]}
          isActive={activeProvider === "ibkr"}
          onActivate={() =>
            handleSwitchProvider("ibkr", {
              host: ibkrHost,
              port: parseInt(ibkrPort),
              client_id: parseInt(ibkrClientId),
            })
          }
          isLoading={switchProvider.isPending}
        >
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Server className="h-4 w-4" />
              Connection Settings
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-xs text-muted-foreground">Host</label>
                <Input
                  value={ibkrHost}
                  onChange={(e) => setIbkrHost(e.target.value)}
                  placeholder="127.0.0.1"
                  className="h-8 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Port</label>
                <Input
                  value={ibkrPort}
                  onChange={(e) => setIbkrPort(e.target.value)}
                  placeholder="7497"
                  className="h-8 text-sm"
                />
              </div>
              <div>
                <label className="text-xs text-muted-foreground">Client ID</label>
                <Input
                  value={ibkrClientId}
                  onChange={(e) => setIbkrClientId(e.target.value)}
                  placeholder="1"
                  className="h-8 text-sm"
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              TWS: 7496 (live) / 7497 (paper) | Gateway: 4001 (live) / 4002 (paper)
            </p>
          </div>
        </ProviderCard>

        {/* SAXO Provider */}
        <ProviderCard
          name="saxo"
          displayName="Saxo Bank"
          description="Premium market data from Saxo Bank OpenAPI. Requires developer account and API access token."
          markets={["US", "JP", "HK"]}
          isActive={activeProvider === "saxo"}
          onActivate={() =>
            handleSwitchProvider("saxo", {
              access_token: saxoToken,
              environment: saxoEnv,
            })
          }
          isLoading={switchProvider.isPending}
        >
          <div className="space-y-3 pt-2 border-t">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Key className="h-4 w-4" />
              API Configuration
            </div>
            <div>
              <label className="text-xs text-muted-foreground">Access Token</label>
              <Input
                type="password"
                value={saxoToken}
                onChange={(e) => setSaxoToken(e.target.value)}
                placeholder="Enter your Saxo API access token"
                className="h-8 text-sm"
              />
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={saxoEnv === "sim" ? "default" : "outline"}
                onClick={() => setSaxoEnv("sim")}
                className="flex-1"
              >
                <Globe className="h-3 w-3 mr-1" />
                Simulation
              </Button>
              <Button
                size="sm"
                variant={saxoEnv === "live" ? "default" : "outline"}
                onClick={() => setSaxoEnv("live")}
                className="flex-1"
              >
                <Check className="h-3 w-3 mr-1" />
                Live
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Get your token from{" "}
              <a
                href="https://www.developer.saxo/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                developer.saxo
              </a>
            </p>
          </div>
        </ProviderCard>
      </div>

      {/* Status */}
      {switchProvider.isError && (
        <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
          Failed to switch provider: {(switchProvider.error as Error)?.message || "Unknown error"}
        </div>
      )}

      {switchProvider.isSuccess && (
        <div className="p-3 bg-bb-green/10 text-bb-green rounded-md text-sm flex items-center gap-2">
          <Check className="h-4 w-4" />
          Provider switched successfully
        </div>
      )}
    </div>
  )
}
