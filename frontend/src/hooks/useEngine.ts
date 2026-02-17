import { useQuery, useMutation } from "@tanstack/react-query"
import {
  getEngineRegime,
  getEngineRegimeHistory,
  getEngineRecommendations,
  getEngineAnalysis,
  getEngineStrategies,
  getEngineStrategiesByFamily,
  getEngineTailRisk,
  getEngineEarlyWarnings,
  getEngineConflicts,
  getEngineActiveConflicts,
  evaluateEnginePosition,
  getEnginePlaybook,
  getEngineZeroDTE,
  getEngineZeroDTEDay,
  getEngineReferenceTables,
  getEngineReferenceTable,
} from "../lib/engineApi"

// ── Regime ───────────────────────────────────────────────────────────────

export function useEngineRegime() {
  return useQuery({
    queryKey: ["engine", "regime"],
    queryFn: getEngineRegime,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

export function useEngineRegimeHistory() {
  return useQuery({
    queryKey: ["engine", "regime", "history"],
    queryFn: getEngineRegimeHistory,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Strategy Recommendations ─────────────────────────────────────────────

export function useEngineRecommendations(
  nav: number = 100_000,
  objective: string = "income"
) {
  return useQuery({
    queryKey: ["engine", "recommendations", nav, objective],
    queryFn: () => getEngineRecommendations(nav, objective),
    refetchInterval: 120_000,
    staleTime: 30_000,
  })
}

// ── Full Analysis ────────────────────────────────────────────────────────

export function useEngineAnalysis(
  nav: number = 100_000,
  objective: string = "income"
) {
  return useQuery({
    queryKey: ["engine", "analysis", nav, objective],
    queryFn: () => getEngineAnalysis(nav, objective),
    refetchInterval: 120_000,
    staleTime: 30_000,
  })
}

// ── Strategy Universe ────────────────────────────────────────────────────

export function useEngineStrategies() {
  return useQuery({
    queryKey: ["engine", "strategies"],
    queryFn: getEngineStrategies,
    staleTime: 600_000,
  })
}

export function useEngineStrategiesByFamily(family: string) {
  return useQuery({
    queryKey: ["engine", "strategies", family],
    queryFn: () => getEngineStrategiesByFamily(family),
    staleTime: 600_000,
    enabled: !!family,
  })
}

// ── Tail Risk ────────────────────────────────────────────────────────────

export function useEngineTailRisk() {
  return useQuery({
    queryKey: ["engine", "tail-risk"],
    queryFn: getEngineTailRisk,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

export function useEngineEarlyWarnings() {
  return useQuery({
    queryKey: ["engine", "early-warnings"],
    queryFn: getEngineEarlyWarnings,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Conflicts ────────────────────────────────────────────────────────────

export function useEngineConflicts() {
  return useQuery({
    queryKey: ["engine", "conflicts"],
    queryFn: getEngineConflicts,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

export function useEngineActiveConflicts() {
  return useQuery({
    queryKey: ["engine", "conflicts", "active"],
    queryFn: getEngineActiveConflicts,
    refetchInterval: 60_000,
    staleTime: 30_000,
  })
}

// ── Position Health ──────────────────────────────────────────────────────

export function useEvaluatePosition() {
  return useMutation({
    mutationFn: (position: Record<string, unknown>) =>
      evaluateEnginePosition(position),
  })
}

// ── Playbooks ────────────────────────────────────────────────────────────

export function useEnginePlaybook(eventType: string) {
  return useQuery({
    queryKey: ["engine", "playbook", eventType],
    queryFn: () => getEnginePlaybook(eventType),
    enabled: !!eventType && eventType !== "NONE",
    staleTime: 600_000,
  })
}

export function useEngineZeroDTE() {
  return useQuery({
    queryKey: ["engine", "playbook", "0dte"],
    queryFn: getEngineZeroDTE,
    staleTime: 600_000,
  })
}

export function useEngineZeroDTEDay(day: string) {
  return useQuery({
    queryKey: ["engine", "playbook", "0dte", day],
    queryFn: () => getEngineZeroDTEDay(day),
    enabled: !!day,
    staleTime: 600_000,
  })
}

// ── Reference Tables ─────────────────────────────────────────────────────

export function useEngineReferenceTables() {
  return useQuery({
    queryKey: ["engine", "reference"],
    queryFn: getEngineReferenceTables,
    staleTime: Infinity,
  })
}

export function useEngineReferenceTable(tableName: string) {
  return useQuery({
    queryKey: ["engine", "reference", tableName],
    queryFn: () => getEngineReferenceTable(tableName),
    enabled: !!tableName,
    staleTime: Infinity,
  })
}
