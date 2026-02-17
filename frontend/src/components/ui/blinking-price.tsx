import { useState, useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

interface BlinkingPriceProps {
  value: number | undefined | null
  previousValue?: number | undefined | null
  format?: (value: number) => string
  showArrow?: boolean
  showChange?: boolean
  changeValue?: number | null
  changePercent?: number | null
  className?: string
  size?: "sm" | "md" | "lg"
}

export function BlinkingPrice({
  value,
  previousValue,
  format = (v) => v.toFixed(2),
  showArrow = false,
  showChange = false,
  changeValue,
  changePercent,
  className,
  size = "md",
}: BlinkingPriceProps) {
  const [flashClass, setFlashClass] = useState<string>("")
  const [direction, setDirection] = useState<"up" | "down" | "neutral">("neutral")
  const prevValueRef = useRef<number | null>(null)
  const animationKey = useRef(0)

  useEffect(() => {
    if (value === undefined || value === null) return

    const prev = previousValue ?? prevValueRef.current

    if (prev !== null && prev !== value) {
      const newDirection = value > prev ? "up" : value < prev ? "down" : "neutral"
      setDirection(newDirection)
      setFlashClass(
        newDirection === "up"
          ? "price-up"
          : newDirection === "down"
          ? "price-down"
          : "price-neutral"
      )
      animationKey.current += 1

      // Clear flash class after animation
      const timer = setTimeout(() => {
        setFlashClass("")
      }, 800)

      return () => clearTimeout(timer)
    }

    prevValueRef.current = value
  }, [value, previousValue])

  // Update ref when value changes
  useEffect(() => {
    if (value !== undefined && value !== null) {
      prevValueRef.current = value
    }
  }, [value])

  if (value === undefined || value === null) {
    return <span className={cn("text-muted-foreground", className)}>---</span>
  }

  const sizeClasses = {
    sm: "text-xs",
    md: "text-sm",
    lg: "text-lg",
  }

  const formattedValue = format(value)

  // Determine color based on change
  const hasPositiveChange = changeValue !== undefined && changeValue !== null && changeValue > 0
  const hasNegativeChange = changeValue !== undefined && changeValue !== null && changeValue < 0
  const colorClass = hasPositiveChange
    ? "text-bb-green"
    : hasNegativeChange
    ? "text-bb-red"
    : ""

  return (
    <span
      key={animationKey.current}
      className={cn(
        "price-value inline-flex items-center gap-1",
        sizeClasses[size],
        flashClass,
        className
      )}
    >
      {showArrow && direction !== "neutral" && (
        <span className={cn("price-arrow", direction)} />
      )}
      <span className={colorClass}>{formattedValue}</span>
      {showChange && (changeValue !== undefined || changePercent !== undefined) && (
        <span
          className={cn(
            "text-[0.85em]",
            hasPositiveChange && "text-bb-green",
            hasNegativeChange && "text-bb-red",
            !hasPositiveChange && !hasNegativeChange && "text-muted-foreground"
          )}
        >
          {changeValue !== undefined && changeValue !== null && (
            <span>
              {changeValue > 0 ? "+" : ""}
              {changeValue.toFixed(2)}
            </span>
          )}
          {changePercent !== undefined && changePercent !== null && (
            <span className="ml-1">
              ({changePercent > 0 ? "+" : ""}
              {changePercent.toFixed(2)}%)
            </span>
          )}
        </span>
      )}
    </span>
  )
}

// Hook for tracking price changes with animation
export function usePriceFlash(currentValue: number | undefined | null) {
  const [flashState, setFlashState] = useState<{
    flash: boolean
    direction: "up" | "down" | "neutral"
  }>({ flash: false, direction: "neutral" })
  const prevValueRef = useRef<number | null>(null)

  useEffect(() => {
    if (currentValue === undefined || currentValue === null) return

    const prev = prevValueRef.current

    if (prev !== null && prev !== currentValue) {
      const direction = currentValue > prev ? "up" : currentValue < prev ? "down" : "neutral"
      setFlashState({ flash: true, direction })

      const timer = setTimeout(() => {
        setFlashState((s) => ({ ...s, flash: false }))
      }, 800)

      prevValueRef.current = currentValue
      return () => clearTimeout(timer)
    }

    prevValueRef.current = currentValue
  }, [currentValue])

  return flashState
}

// Simple flash wrapper component
export function FlashOnChange({
  value,
  children,
  className,
}: {
  value: unknown
  children: React.ReactNode
  className?: string
}) {
  const [flash, setFlash] = useState(false)
  const prevValueRef = useRef<unknown>(null)
  const key = useRef(0)

  useEffect(() => {
    if (prevValueRef.current !== null && prevValueRef.current !== value) {
      setFlash(true)
      key.current += 1
      const timer = setTimeout(() => setFlash(false), 800)
      return () => clearTimeout(timer)
    }
    prevValueRef.current = value
  }, [value])

  return (
    <span key={key.current} className={cn(flash && "price-neutral", className)}>
      {children}
    </span>
  )
}
