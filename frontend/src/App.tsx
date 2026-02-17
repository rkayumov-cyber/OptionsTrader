import { useState, useEffect, useCallback, useRef } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { IndexTicker } from "@/components/IndexTicker"
import { Settings } from "@/components/Settings"
import { MarketDashboard } from "@/components/dashboard"
import { SymbolAnalysis } from "@/components/analysis"
import { TradingPage, RiskPage } from "@/components/pages"
import { useProviders, useSwitchProvider } from "@/hooks/useMarketData"
import {
  Settings as SettingsIcon,
  LayoutDashboard,
  TrendingUp,
  Briefcase,
  AlertTriangle,
  Terminal,
  X,
  Keyboard,
  Command,
} from "lucide-react"
import type { Market } from "@/lib/api"
import RegimeDashboard from "@/components/engine/RegimeDashboard"
import StrategyRecommendations from "@/components/engine/StrategyRecommendations"
import PositionHealthCheckComponent from "@/components/engine/PositionHealthCheck"
import TailRiskPanel from "@/components/engine/TailRiskPanel"
import EventPlaybookViewer from "@/components/engine/EventPlaybookViewer"
import ReferenceTableViewer from "@/components/engine/ReferenceTableViewer"
import ConflictAlert from "@/components/engine/ConflictAlert"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

function ProviderSelector() {
  const { data: providers } = useProviders()
  const switchProvider = useSwitchProvider()

  if (!providers) return null

  return (
    <Select
      value={providers.active}
      onChange={(e) => switchProvider.mutate({ provider: e.target.value })}
      className="w-24 h-6 text-[10px]"
    >
      {providers.available.map((p) => (
        <option key={p.name} value={p.name}>
          {p.name.toUpperCase()}
        </option>
      ))}
    </Select>
  )
}

function Clock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <span className="font-mono tabular-nums">
      {time.toLocaleTimeString("en-US", { hour12: false })}
    </span>
  )
}

type ViewType = "analyze" | "dashboard" | "trading" | "risk" | "engine" | "settings"

type NavItem = {
  view: ViewType
  label: string
  icon: React.ReactNode
  shortcut: string
  command: string
}

const NAV_ITEMS: NavItem[] = [
  { view: "analyze",   label: "Analyze",   icon: <TrendingUp className="h-3.5 w-3.5" />,      shortcut: "F1", command: "A" },
  { view: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="h-3.5 w-3.5" />, shortcut: "F2", command: "DASH" },
  { view: "trading",   label: "Trade",     icon: <Briefcase className="h-3.5 w-3.5" />,       shortcut: "F3", command: "TRADE" },
  { view: "risk",      label: "Risk",      icon: <AlertTriangle className="h-3.5 w-3.5" />,   shortcut: "F4", command: "RISK" },
  { view: "engine",    label: "Engine",    icon: <Terminal className="h-3.5 w-3.5" />,         shortcut: "F5", command: "ENGINE" },
]

// Command routes - maps commands to view + tab for deep-linking
const COMMAND_ROUTES: Record<string, { view: ViewType; tab?: string }> = {
  // Page-level commands
  "A":      { view: "analyze" },
  "DASH":   { view: "dashboard" },
  "TRADE":  { view: "trading" },
  "RISK":   { view: "risk" },
  "ENGINE": { view: "engine" },
  "REGIME": { view: "engine", tab: "regime" },
  "REC":    { view: "engine", tab: "recommendations" },
  "TAIL":   { view: "engine", tab: "tail-risk" },
  // Analyze tabs
  "Q":      { view: "analyze", tab: "overview" },
  "MKT":    { view: "analyze", tab: "overview" },
  "OPT":    { view: "analyze", tab: "options" },
  "VOL":    { view: "analyze", tab: "volatility" },
  "3D":     { view: "analyze", tab: "volatility" },
  "IV":     { view: "analyze", tab: "volatility" },
  "TERM":   { view: "analyze", tab: "volatility" },
  "SKEW":   { view: "analyze", tab: "volatility" },
  "PAY":    { view: "analyze", tab: "strategy" },
  "PROB":   { view: "analyze", tab: "strategy" },
  "JPM":    { view: "analyze", tab: "research" },
  "EARN":   { view: "analyze", tab: "research" },
  // Trading tabs
  "POS":    { view: "trading", tab: "positions" },
  "PAPER":  { view: "trading", tab: "paper" },
  "JRNL":   { view: "trading", tab: "journal" },
  "ALRT":   { view: "trading", tab: "alerts" },
  // Risk tabs
  "SCAN":   { view: "risk", tab: "scanner" },
  "CORR":   { view: "risk", tab: "correlation" },
  "STRESS": { view: "risk", tab: "stress" },
}

// Keyboard shortcuts help modal
function KeyboardShortcutsModal({ onClose }: { onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-card border border-border rounded max-w-2xl w-full max-h-[80vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted">
          <div className="flex items-center gap-2">
            <Keyboard className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold text-primary uppercase tracking-wider">Keyboard Shortcuts</span>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="p-4 space-y-4">
          {/* Global shortcuts */}
          <div>
            <h3 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Global</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Command bar</span>
                <kbd className="bb-kbd">/</kbd>
              </div>
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">This help</span>
                <kbd className="bb-kbd">?</kbd>
              </div>
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Settings</span>
                <kbd className="bb-kbd">Ctrl+,</kbd>
              </div>
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Close/Cancel</span>
                <kbd className="bb-kbd">Esc</kbd>
              </div>
            </div>
          </div>

          {/* Navigation shortcuts */}
          <div>
            <h3 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Navigation</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {NAV_ITEMS.map((item) => (
                <div key={item.view} className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                  <span className="text-muted-foreground">{item.label}</span>
                  <div className="flex items-center gap-1">
                    <kbd className="bb-kbd">{item.shortcut}</kbd>
                    <span className="text-bb-cyan text-[10px]">{item.command}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Command bar deep-links */}
          <div>
            <h3 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Command Bar Deep-Links</h3>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {Object.entries(COMMAND_ROUTES)
                .filter(([, route]) => route.tab)
                .map(([cmd, route]) => (
                  <div key={cmd} className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                    <span className="text-muted-foreground capitalize">{route.tab?.replace("-", " ")}</span>
                    <span className="text-bb-cyan text-[10px]">{cmd}</span>
                  </div>
                ))}
            </div>
          </div>

          {/* Symbol navigation */}
          <div>
            <h3 className="text-xs font-semibold text-primary uppercase tracking-wider mb-2">Symbol Entry</h3>
            <div className="grid grid-cols-1 gap-2 text-xs">
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Enter symbol (e.g., "AAPL", "TSLA US")</span>
                <div className="flex items-center gap-1">
                  <kbd className="bb-kbd">/</kbd>
                  <span className="text-bb-cyan">symbol</span>
                  <kbd className="bb-kbd">Enter</kbd>
                </div>
              </div>
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Analyze symbol overview</span>
                <div className="flex items-center gap-1">
                  <kbd className="bb-kbd">/</kbd>
                  <span className="text-bb-cyan">AAPL</span>
                  <kbd className="bb-kbd">Enter</kbd>
                </div>
              </div>
              <div className="flex items-center justify-between px-2 py-1 bg-muted/50 rounded">
                <span className="text-muted-foreground">Go to options chain</span>
                <div className="flex items-center gap-1">
                  <kbd className="bb-kbd">/</kbd>
                  <span className="text-bb-cyan">AAPL OPT</span>
                  <kbd className="bb-kbd">Enter</kbd>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="px-4 py-2 border-t border-border bg-muted/50 text-[10px] text-muted-foreground text-center">
          Press <kbd className="bb-kbd">Esc</kbd> or click outside to close
        </div>
      </div>
    </div>
  )
}

// Command bar component
function CommandBar({
  onClose,
  onNavigate,
  onSymbolChange,
}: {
  onClose: () => void
  onNavigate: (view: ViewType, tab?: string) => void
  onSymbolChange: (symbol: string, market: Market) => void
}) {
  const [input, setInput] = useState("")
  const [suggestions, setSuggestions] = useState<{ label: string; command: string; view: ViewType; tab?: string }[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  useEffect(() => {
    const query = input.toUpperCase().trim()
    if (!query) {
      setSuggestions([])
      return
    }

    // Build suggestion list from COMMAND_ROUTES and NAV_ITEMS
    const matches: { label: string; command: string; view: ViewType; tab?: string }[] = []
    for (const [cmd, route] of Object.entries(COMMAND_ROUTES)) {
      if (cmd.includes(query) || route.view.toUpperCase().includes(query) || (route.tab && route.tab.toUpperCase().includes(query))) {
        const navItem = NAV_ITEMS.find(n => n.view === route.view)
        const label = route.tab
          ? `${navItem?.label || route.view} > ${route.tab.replace(/-/g, " ")}`
          : navItem?.label || route.view
        matches.push({ label, command: cmd, view: route.view, tab: route.tab })
      }
    }
    setSuggestions(matches.slice(0, 8))
  }, [input])

  const parseMarket = (raw: string): { symbol: string; market: Market } => {
    let market: Market = "US"
    let symbol = raw
    if (raw.endsWith(" JP") || raw.endsWith(".T")) {
      market = "JP"
      symbol = raw.replace(/ JP$/, "").replace(/\.T$/, "")
    } else if (raw.endsWith(" HK") || raw.match(/^\d{4,5}$/)) {
      market = "HK"
      symbol = raw.replace(/ HK$/, "")
    } else if (raw.endsWith(" US")) {
      symbol = raw.replace(/ US$/, "")
    }
    return { symbol, market }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const query = input.toUpperCase().trim()

    if (!query) {
      onClose()
      return
    }

    const parts = query.split(/\s+/)

    // Check if the entire query is a single command
    if (parts.length === 1 && COMMAND_ROUTES[parts[0]]) {
      const route = COMMAND_ROUTES[parts[0]]
      onNavigate(route.view, route.tab)
      onClose()
      return
    }

    // Check last part for a command (e.g., "AAPL OPT", "TSLA VOL")
    if (parts.length >= 2) {
      const lastPart = parts[parts.length - 1]
      const route = COMMAND_ROUTES[lastPart]

      if (route) {
        const symbolRaw = parts.slice(0, -1).join(" ")
        const { symbol, market } = parseMarket(symbolRaw)
        onSymbolChange(symbol, market)
        onNavigate(route.view, route.tab)
        onClose()
        return
      }
    }

    // Assume it's just a symbol - go to analyze page, overview tab
    const { symbol, market } = parseMarket(query)
    onSymbolChange(symbol, market)
    onNavigate("analyze", "overview")
    onClose()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-start justify-center pt-[20vh]" onClick={onClose}>
      <div
        className="bg-card border border-primary rounded w-full max-w-lg shadow-lg shadow-primary/20"
        onClick={(e) => e.stopPropagation()}
      >
        <form onSubmit={handleSubmit}>
          <div className="flex items-center gap-2 px-3 py-2 border-b border-border">
            <Command className="h-4 w-4 text-primary" />
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value.toUpperCase())}
              onKeyDown={handleKeyDown}
              placeholder="Enter symbol or command (e.g., AAPL, OPT, AAPL VOL)"
              className="flex-1 border-0 bg-transparent focus-visible:ring-0 text-sm uppercase"
              autoComplete="off"
              spellCheck={false}
            />
            <kbd className="bb-kbd text-[10px]">Enter</kbd>
          </div>
        </form>

        {suggestions.length > 0 && (
          <div className="border-t border-border">
            {suggestions.map((item) => (
              <button
                key={`${item.view}-${item.tab || "default"}`}
                onClick={() => {
                  onNavigate(item.view, item.tab)
                  onClose()
                }}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-muted/50 text-left"
              >
                <span className="text-sm capitalize">{item.label}</span>
                <span className="text-bb-cyan text-xs ml-auto">{item.command}</span>
              </button>
            ))}
          </div>
        )}

        <div className="px-3 py-1.5 border-t border-border bg-muted/30 text-[10px] text-muted-foreground">
          <span className="text-bb-amber">TIP:</span> Type a symbol to analyze it, or add a command: <span className="text-bb-cyan">AAPL OPT</span> for options chain
        </div>
      </div>
    </div>
  )
}

function EnginePage() {
  const [tab, setTab] = useState("overview")
  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "recommendations", label: "Strategies" },
    { id: "health", label: "Position Health" },
    { id: "tail-risk", label: "Tail Risk" },
    { id: "playbooks", label: "Playbooks" },
    { id: "reference", label: "Reference" },
  ]

  return (
    <div className="space-y-3 p-4">
      {/* Engine Tabs */}
      <div className="flex gap-1 border-b border-zinc-800 pb-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-t text-xs transition-colors ${
              tab === t.id
                ? "bg-zinc-800 text-zinc-200 border-b-2 border-blue-500"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Conflict Banner (always visible) */}
      <ConflictAlert />

      {/* Tab Content */}
      {tab === "overview" && (
        <div className="grid grid-cols-2 gap-4">
          <RegimeDashboard />
          <StrategyRecommendations />
        </div>
      )}

      {tab === "recommendations" && <StrategyRecommendations />}
      {tab === "health" && <PositionHealthCheckComponent />}
      {tab === "tail-risk" && <TailRiskPanel />}
      {tab === "playbooks" && <EventPlaybookViewer />}
      {tab === "reference" && <ReferenceTableViewer />}
    </div>
  )
}

function Dashboard() {
  const [activeView, setActiveView] = useState<ViewType>("analyze")
  const [activeTab, setActiveTab] = useState<string | undefined>(undefined)
  const [selectedSymbol, setSelectedSymbol] = useState("SPY")
  const [selectedMarket, setSelectedMarket] = useState<Market>("US")
  const [showShortcuts, setShowShortcuts] = useState(false)
  const [showCommandBar, setShowCommandBar] = useState(false)

  const handleSymbolSelect = (symbol: string, market: Market) => {
    setSelectedSymbol(symbol)
    setSelectedMarket(market)
  }

  const handleViewSymbolDetails = (symbol: string, market: Market) => {
    setSelectedSymbol(symbol)
    setSelectedMarket(market)
    setActiveView("analyze")
    setActiveTab("overview")
  }

  const handleNavigate = (view: ViewType, tab?: string) => {
    setActiveView(view)
    setActiveTab(tab)
  }

  // Clear activeTab when user clicks a nav button directly (no deep-link)
  const handleNavClick = (view: ViewType) => {
    setActiveView(view)
    setActiveTab(undefined)
  }

  // Keyboard shortcuts handler
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Don't trigger shortcuts when typing in inputs
    const target = e.target as HTMLElement
    if (target.tagName === "INPUT" || target.tagName === "TEXTAREA" || target.isContentEditable) {
      if (e.key === "Escape") {
        setShowCommandBar(false)
        setShowShortcuts(false)
        target.blur()
      }
      return
    }

    // Command bar
    if (e.key === "/" && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      setShowCommandBar(true)
      return
    }

    // Help
    if (e.key === "?" && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      setShowShortcuts(true)
      return
    }

    // Escape to close modals
    if (e.key === "Escape") {
      setShowCommandBar(false)
      setShowShortcuts(false)
      return
    }

    // Settings
    if ((e.key === "," && (e.ctrlKey || e.metaKey))) {
      e.preventDefault()
      setActiveView("settings")
      setActiveTab(undefined)
      return
    }

    // Function keys F1-F5
    const fKeyMatch = e.key.match(/^F(\d+)$/)
    if (fKeyMatch && !e.altKey && !e.ctrlKey && !e.metaKey) {
      const fNum = parseInt(fKeyMatch[1])
      const fKeyMap: Record<number, ViewType> = {
        1: "analyze",
        2: "dashboard",
        3: "trading",
        4: "risk",
        5: "engine",
      }
      if (fKeyMap[fNum]) {
        e.preventDefault()
        setActiveView(fKeyMap[fNum])
        setActiveTab(undefined)
        return
      }
    }
  }, [])

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  const currentNavItem = NAV_ITEMS.find(i => i.view === activeView)
  const currentViewLabel = currentNavItem?.label || (activeView === "settings" ? "Settings" : "Analyze")
  const currentShortcut = currentNavItem?.shortcut

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Modals */}
      {showShortcuts && <KeyboardShortcutsModal onClose={() => setShowShortcuts(false)} />}
      {showCommandBar && (
        <CommandBar
          onClose={() => setShowCommandBar(false)}
          onNavigate={handleNavigate}
          onSymbolChange={handleSymbolSelect}
        />
      )}

      {/* Bloomberg-style Header */}
      <header className="bg-muted border-b border-border">
        {/* Top bar with branding and time */}
        <div className="flex items-center justify-between px-3 py-1 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-primary" />
              <span className="text-sm font-bold text-primary tracking-wider">OPTIONS TRADER</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Cross-Market Terminal
            </span>
          </div>
          <div className="flex items-center gap-4 text-[11px]">
            {/* Command bar trigger */}
            <button
              onClick={() => setShowCommandBar(true)}
              className="flex items-center gap-2 px-2 py-0.5 bg-secondary rounded hover:bg-secondary/80 transition-colors"
            >
              <Command className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Command</span>
              <kbd className="bb-kbd text-[9px]">/</kbd>
            </button>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground">PROVIDER:</span>
              <ProviderSelector />
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="flex items-center gap-2">
              <span className="live-indicator" />
              <span className="text-bb-green">LIVE</span>
            </div>
            <div className="h-4 w-px bg-border" />
            <div className="text-muted-foreground">
              <Clock />
            </div>
          </div>
        </div>

        {/* Navigation bar - single flat row */}
        <div className="flex items-center justify-between px-2 py-1">
          <nav className="flex items-center gap-0.5">
            {NAV_ITEMS.map((item) => (
              <Button
                key={item.view}
                variant={activeView === item.view ? "default" : "ghost"}
                size="sm"
                onClick={() => handleNavClick(item.view)}
                className={`h-6 px-2.5 gap-1.5 text-[11px] ${
                  activeView === item.view
                    ? "bg-primary text-primary-foreground"
                    : "text-foreground hover:text-primary"
                }`}
                title={`${item.label} (${item.shortcut})`}
              >
                {item.icon}
                <span>{item.label}</span>
                <kbd className="bb-kbd text-[9px] ml-0.5 hidden lg:inline">{item.shortcut}</kbd>
              </Button>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            {selectedSymbol && activeView !== "dashboard" && (
              <div className="flex items-center gap-1 px-2 py-0.5 bg-secondary rounded text-[11px]">
                <span className="text-bb-cyan font-semibold">{selectedSymbol}</span>
                <span className="text-muted-foreground">({selectedMarket})</span>
              </div>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowShortcuts(true)}
              className="h-6 w-6 p-0"
              title="Keyboard Shortcuts (?)"
            >
              <Keyboard className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant={activeView === "settings" ? "default" : "ghost"}
              size="sm"
              onClick={() => handleNavClick("settings")}
              className="h-6 w-6 p-0"
              title="Settings (Ctrl+,)"
            >
              <SettingsIcon className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Index Ticker */}
      <IndexTicker />

      {/* View Title Bar */}
      <div className="bg-muted/50 border-b border-border px-3 py-1 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-primary font-semibold text-xs uppercase tracking-wider">
            {currentViewLabel}
          </span>
          {currentShortcut && (
            <kbd className="bb-kbd text-[9px]">{currentShortcut}</kbd>
          )}
          {activeView === "analyze" && selectedSymbol && (
            <>
              <span className="text-muted-foreground">/</span>
              <span className="text-bb-cyan font-semibold text-xs">{selectedSymbol}</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span>Press <kbd className="bb-kbd text-[9px]">/</kbd> for commands</span>
          <span className="text-border">|</span>
          <span>{new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" })}</span>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-3">
          {activeView === "analyze" && (
            <SymbolAnalysis
              symbol={selectedSymbol}
              market={selectedMarket}
              onSymbolChange={handleSymbolSelect}
              defaultTab={activeTab}
            />
          )}

          {activeView === "dashboard" && (
            <MarketDashboard
              onSymbolSelect={handleViewSymbolDetails}
              selectedSymbol={selectedSymbol}
              selectedMarket={selectedMarket}
            />
          )}

          {activeView === "trading" && (
            <TradingPage defaultTab={activeTab} />
          )}

          {activeView === "risk" && (
            <RiskPage
              defaultTab={activeTab}
              onSelectSymbol={handleViewSymbolDetails}
            />
          )}

          {activeView === "engine" && <EnginePage />}

          {activeView === "settings" && <Settings />}
        </div>
      </main>

      {/* Bloomberg-style Status Bar */}
      <footer className="bb-status-bar text-[10px]">
        <div className="flex items-center gap-4">
          <div className="bb-status-item">
            <span className="bb-status-label">US</span>
            <span className="text-bb-green">OPEN</span>
          </div>
          <div className="bb-status-item">
            <span className="bb-status-label">JP</span>
            <span className="text-bb-red">CLOSED</span>
          </div>
          <div className="bb-status-item">
            <span className="bb-status-label">HK</span>
            <span className="text-bb-red">CLOSED</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowShortcuts(true)}
            className="hover:text-primary transition-colors"
          >
            <kbd className="bb-kbd text-[9px]">?</kbd> Help
          </button>
          <span className="text-muted-foreground">|</span>
          <span>OPTIONS TRADER TERMINAL v0.1.0</span>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  )
}

export default App
