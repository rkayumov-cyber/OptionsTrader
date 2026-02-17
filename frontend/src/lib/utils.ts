import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatPrice(price: number | null | undefined, currency: string = "USD"): string {
  if (price === null || price === undefined) return "-"

  const symbols: Record<string, string> = {
    USD: "$",
    JPY: "¥",
    HKD: "HK$",
  }

  const symbol = symbols[currency] || "$"
  return `${symbol}${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-"
  return `${(value * 100).toFixed(2)}%`
}

export function formatVolume(volume: number | null | undefined): string {
  if (volume === null || volume === undefined) return "-"
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(1)}K`
  return volume.toString()
}

export function formatGreek(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-"
  return value.toFixed(4)
}
