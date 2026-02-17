import { useState, useEffect, useCallback } from "react"
import {
  getMCPServers,
  toggleMCPServer,
  reconnectMCPServer,
  type MCPServerStatus,
} from "@/lib/api"

interface MCPServersPanelProps {
  className?: string
}

export function MCPServersPanel({ className = "" }: MCPServersPanelProps) {
  const [servers, setServers] = useState<MCPServerStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const fetchServers = useCallback(async () => {
    try {
      const { servers: data } = await getMCPServers()
      setServers(data)
    } catch {
      // MCP manager may not be ready yet
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchServers()
    const interval = setInterval(fetchServers, 15000)
    return () => clearInterval(interval)
  }, [fetchServers])

  const handleToggle = async (serverId: string) => {
    setActionLoading(serverId)
    try {
      const updated = await toggleMCPServer(serverId)
      setServers((prev) =>
        prev.map((s) => (s.id === serverId ? updated : s))
      )
    } catch {
      // ignore
    } finally {
      setActionLoading(null)
    }
  }

  const handleReconnect = async (serverId: string) => {
    setActionLoading(serverId)
    try {
      const updated = await reconnectMCPServer(serverId)
      setServers((prev) =>
        prev.map((s) => (s.id === serverId ? updated : s))
      )
    } catch {
      // ignore
    } finally {
      setActionLoading(null)
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "bg-emerald-400"
      case "connecting":
        return "bg-yellow-400 animate-pulse"
      case "error":
        return "bg-red-400"
      default:
        return "bg-zinc-500"
    }
  }

  if (loading) {
    return (
      <div className={`bg-zinc-900/80 border border-zinc-700/50 rounded p-3 ${className}`}>
        <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium mb-2">
          MCP Data Sources
        </div>
        <div className="text-[10px] text-zinc-600 animate-pulse">Loading...</div>
      </div>
    )
  }

  if (servers.length === 0) {
    return null
  }

  return (
    <div className={`bg-zinc-900/80 border border-zinc-700/50 rounded p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-[10px] text-zinc-500 uppercase tracking-wider font-medium">
          MCP Data Sources
        </div>
        <div className="text-[9px] text-zinc-600">
          {servers.filter((s) => s.status === "connected").length}/{servers.length} connected
        </div>
      </div>

      <div className="space-y-1.5">
        {servers.map((server) => (
          <div
            key={server.id}
            className="flex items-center gap-2 text-[10px] group"
          >
            {/* Status dot */}
            <div
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusColor(server.status)}`}
              title={server.status}
            />

            {/* Name */}
            <span className="text-zinc-300 truncate min-w-0 flex-1">
              {server.name}
            </span>

            {/* Tools count */}
            {server.status === "connected" && (
              <span
                className="text-zinc-500 shrink-0 cursor-help"
                title={server.tools.join(", ")}
              >
                {server.tool_count} tools
              </span>
            )}

            {/* Call stats */}
            {server.call_count > 0 && (
              <span className="text-zinc-600 shrink-0">
                {server.call_count} calls · {Math.round(server.avg_response_ms)}ms
              </span>
            )}

            {/* Error message */}
            {server.status === "error" && server.error && (
              <span className="text-red-400/70 truncate max-w-[120px]" title={server.error}>
                {server.error}
              </span>
            )}

            {/* Actions */}
            <div className="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
              {/* Toggle */}
              <button
                onClick={() => handleToggle(server.id)}
                disabled={actionLoading === server.id}
                className={`px-1.5 py-0.5 rounded text-[9px] transition-colors ${
                  server.enabled
                    ? "bg-zinc-700 text-zinc-300 hover:bg-zinc-600"
                    : "bg-zinc-800 text-zinc-500 hover:bg-zinc-700"
                }`}
                title={server.enabled ? "Disable" : "Enable"}
              >
                {server.enabled ? "ON" : "OFF"}
              </button>

              {/* Reconnect (only for error/disconnected) */}
              {server.enabled && server.status !== "connected" && (
                <button
                  onClick={() => handleReconnect(server.id)}
                  disabled={actionLoading === server.id}
                  className="px-1.5 py-0.5 rounded text-[9px] bg-zinc-800 text-yellow-400/70 hover:bg-zinc-700 transition-colors"
                  title="Reconnect"
                >
                  ↻
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Capabilities summary */}
      {servers.some((s) => s.status === "connected") && (
        <div className="mt-2 pt-1.5 border-t border-zinc-800">
          <div className="flex flex-wrap gap-1">
            {[
              ...new Set(
                servers
                  .filter((s) => s.status === "connected")
                  .flatMap((s) => s.capabilities)
              ),
            ].map((cap) => (
              <span
                key={cap}
                className="px-1.5 py-0.5 rounded bg-zinc-800 text-[9px] text-zinc-400"
              >
                {cap}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
