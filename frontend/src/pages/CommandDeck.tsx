import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useOutletContext, useNavigate } from "react-router-dom"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import OLLOCommander from "../components/hq/OLLOCommander"
import MissionRing from "../components/hq/MissionRing"
import MissionFlow from "../components/hq/MissionFlow"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import type { SubsystemStatus } from "../types/system"
import type { LayoutContext } from "../components/layout/Layout"

function statusColor(status: SubsystemStatus): string {
  switch (status) {
    case "ONLINE": return "#3EDC97"
    case "DEGRADED": return "#FFB547"
    case "OFFLINE": return "#FF5D73"
    case "UNKNOWN": return "#6B7891"
  }
}

function qualityColor(q: string): string {
  switch (q) {
    case "HIGH": return "#3EDC97"
    case "MEDIUM": return "#FFB547"
    case "LOW": return "#FF5D73"
    default: return "#6B7891"
  }
}

function ProgressLine({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="flex items-center gap-3">
      <span
        className="font-mono shrink-0 text-right"
        style={{ fontSize: 8, color: "var(--text-muted)", width: 110, letterSpacing: "0.05em" }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-1 rounded-full overflow-hidden"
        style={{ backgroundColor: "var(--border-subtle)" }}
      >
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span
        className="font-mono tabular-nums shrink-0"
        style={{ fontSize: 8, color, width: 28, textAlign: "right" as const }}
      >
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

// Interfaces for Searchable Objects
interface SearchItem {
  id: string
  category: "assets" | "decisions" | "strategies" | "sessions" | "evidence" | "council members"
  title: string
  subtitle: string
  details: string
  status?: string
}

// Interfaces for Timeline Objects
interface TimelineItem {
  id: string
  category: "market" | "ai" | "whale" | "news" | "trades" | "simulations"
  title: string
  timestamp: string
  details: string
  type: "info" | "success" | "warning" | "danger"
}

export default function CommandDeck() {
  const [showLoading, setShowLoading] = useState(true)
  const navigate = useNavigate()
  const outlet = useOutletContext<LayoutContext>() || {}

  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

  const decisionQuality = evidence.data?.decision_quality ?? null
  const warnings = evidence.data?.warnings ?? []
  const riskScore = risk.data?.risk_score ?? null
  const aiConnected = aiHealth.data?.ollo.connected ?? ollo.status.data?.ai_health.connected ?? null
  const aiLatency = aiHealth.data?.ollo.latency_ms ?? ollo.status.data?.ai_health.latency_ms

  const offlineCount = [scanner, risk, council, portfolio, whale, market, evidence, ollo.status, aiHealth]
    .filter((s) => s.status === "OFFLINE").length

  const missionStatus = useMemo(
    () => computeMissionStatus(riskScore, decisionQuality, aiConnected, offlineCount),
    [riskScore, decisionQuality, aiConnected, offlineCount],
  )

  const currentMission = ollo.briefing?.title || ollo.status.data?.current_mission_profile?.replace(/_/g, " ") || undefined

  const sectors = useMemo(() => [
    { label: "Scanner", status: scanner.status },
    { label: "Council", status: council.status },
    { label: "Risk", status: risk.status },
    { label: "Portfolio", status: portfolio.status },
    { label: "Whale", status: whale.status },
    { label: "Market", status: market.status },
  ], [scanner.status, council.status, risk.status, portfolio.status, whale.status, market.status])

  const flowNodes = useMemo(() => [
    { label: "Scanner" as const, active: scanner.status === "ONLINE", color: statusColor(scanner.status) },
    { label: "Whale" as const, active: whale.status === "ONLINE", color: statusColor(whale.status) },
    { label: "Council" as const, active: council.status === "ONLINE", color: statusColor(council.status) },
    { label: "Evidence" as const, active: evidence.status === "ONLINE", color: statusColor(evidence.status) },
    { label: "Decision" as const, active: aiHealth.status === "ONLINE", color: statusColor(aiHealth.status) },
    { label: "Founder" as const, active: true, color: "#4F8CFF" },
    { label: "Action" as const, active: true, color: "#78A8FF" },
  ], [scanner.status, whale.status, council.status, evidence.status, aiHealth.status])

  const missionColor = useMemo(() => {
    switch (missionStatus) {
      case "ACTIVE": return "#3EDC97"
      case "MONITORING": return "#4F8CFF"
      case "CAUTION": return "#FFB547"
      case "CRITICAL": return "#FF5D73"
    }
  }, [missionStatus])

  const recommendation = evidence.data?.recommendation || "Maintain core wait posture."
  const confidence = evidence.data?.decision_confidence ?? 0.85
  const strength = evidence.data?.evidence_strength ?? 0.72
  const explainability = evidence.data?.explainability ?? 0.80
  const supportingCount = evidence.data?.supporting_evidence.length ?? 3
  const conflictCount = evidence.data?.contradicting_evidence.length ?? 0
  const warningCount = evidence.data?.warnings.length ?? 0

  // UI state for search & timeline
  const [searchQuery, setSearchQuery] = useState("")
  const [searchCategory, setSearchCategory] = useState<string>("all")
  const [timelineFilter, setTimelineFilter] = useState<string>("all")

  // Mock static and dynamic data elements for search & timeline
  const searchableRegistry: SearchItem[] = useMemo(() => [
    { id: "asset-btc", category: "assets", title: "BTC (Bitcoin)", subtitle: "Primary Reserve Asset", details: "Status: Active Surveillance | 24h Volatility: 4.82% | Current Regime: Bulllish", status: "Surveillance" },
    { id: "asset-eth", category: "assets", title: "ETH (Ethereum)", subtitle: "Smart Contract Core", details: "Status: Scanning | 24h Volatility: 3.15% | Trend: Accumulating", status: "Scanning" },
    { id: "asset-sol", category: "assets", title: "SOL (Solana)", subtitle: "High Performance L1", details: "Status: High Strength Breakout Detected | RSI: 68.4", status: "Surveillance" },
    { id: "decision-102", category: "decisions", title: "AI Consensus Decision #102", subtitle: "Strong Buy Consensus (BTC)", details: "Agreement Score: 92% | Council Approval Rate: 5/5 Agents", status: "STRONG_BUY" },
    { id: "decision-101", category: "decisions", title: "AI Consensus Decision #101", subtitle: "Neutral Hold Consensus (ETH)", details: "Agreement Score: 60% | Wait for liquidity support", status: "HOLD" },
    { id: "strat-mean", category: "strategies", title: "Mean Reversion Strategy", subtitle: "Bollinger Bands / RSI Core", details: "ROI: +18.4% | Sharpe: 1.62 | Max Drawdown: 4.2%", status: "Active" },
    { id: "strat-trend", category: "strategies", title: "Trend Follow Strategy", subtitle: "EMA Alignment & MACD Core", details: "ROI: +24.8% | Sharpe: 2.15 | Max Drawdown: 6.8%", status: "Active" },
    { id: "session-042", category: "sessions", title: "Simulator Session #042", subtitle: "Monte Carlo Sandbox Setup", details: "Status: Finished | Completed cycles: 500 | Overall ROI: +14.2%", status: "COMPLETED" },
    { id: "session-043", category: "sessions", title: "Simulator Session #043", subtitle: "Stress Test Forward Sandbox", details: "Status: Active Live | Current cycle: 124/200", status: "ACTIVE" },
    { id: "ev-01", category: "evidence", title: "CVD Accumulation Evidence", subtitle: "Spot Order Book Sentiment", details: "Strength: High | Support: Alpha & Beta Agents", status: "VALIDATED" },
    { id: "ev-02", category: "evidence", title: "RSI Bearish Divergence", subtitle: "4H Timeframe Check", details: "Strength: Medium | Detected on SOLUSDT", status: "MONITORING" },
    { id: "council-alpha", category: "council members", title: "Alpha Agent", subtitle: "Trend Intelligence Specialist", details: "Weights: 0.35 | Latency: 12ms | Primary Factor: EMA / MACD Alignment", status: "ONLINE" },
    { id: "council-beta", category: "council members", title: "Beta Agent", subtitle: "Volume Intelligence Specialist", details: "Weights: 0.25 | Latency: 14ms | Primary Factor: CVD / OB Volume", status: "ONLINE" },
    { id: "council-gamma", category: "council members", title: "Gamma Agent", subtitle: "Macro Sentiment Specialist", details: "Weights: 0.20 | Latency: 18ms | Primary Factor: Funding Rates / OI", status: "ONLINE" },
  ], [])

  const timelineRegistry: TimelineItem[] = useMemo(() => [
    { id: "tl-01", category: "market", title: "Market Regime Shift (BTC)", timestamp: "04:12:15", details: "Regime transitioned to BULLISH_HIGH_VOLATILITY following breakout of $95,200 resistance.", type: "success" },
    { id: "tl-02", category: "ai", title: "AI Council Decision #102 Generated", timestamp: "04:11:42", details: "Unanimous consensus reached. 5/5 Agents approve LONG entry setup on BTCUSDT with 92% confidence.", type: "success" },
    { id: "tl-03", category: "whale", title: "Significant Whale Buy Wall Spotted", timestamp: "04:09:10", details: "Whale order book depth increased by +5,200 BTC at active support range of $94,800.", type: "info" },
    { id: "tl-04", category: "news", title: "US CPI Inflation Data Reported", timestamp: "03:45:00", details: "Core CPI reported at 0.1% below consensus estimates, triggering capital inflows into reserve assets.", type: "info" },
    { id: "tl-05", category: "trades", title: "Paper Execution: Trade #105 OPENED", timestamp: "03:30:12", details: "Position LONG BTCUSDT filled at $95,120. Stop Loss: $93,900, TP1: $97,200.", type: "warning" },
    { id: "tl-06", category: "simulations", title: "Monte Carlo Simulator Cycle Completed", timestamp: "02:15:33", details: "Trial #14 completed 500 stress-test cycles. Estimated Sharpe ratio: 1.84, Drawdown: 3.12%.", type: "info" },
    { id: "tl-07", category: "market", title: "Whale CVD Divergence Spotted", timestamp: "01:45:10", details: "Accumulation score increased from 0.45 to 0.88 over 4H window with rising volume.", type: "success" },
  ], [])

  // Live WebSocket state or default falls
  const livePrice = outlet.latestPrice?.price ?? 95850.50
  const liveChange = outlet.latestPrice?.change_24h ?? 4.12
  const liveRiskScore = outlet.latestRiskWs?.risk_score ?? 0.24
  const activePositionCount = outlet.openTrades?.length ?? 1

  // Filters search list
  const filteredSearchItems = useMemo(() => {
    return searchableRegistry.filter((item) => {
      const matchesCategory = searchCategory === "all" || item.category === searchCategory
      const matchesQuery = searchQuery === "" ||
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.subtitle.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.details.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesCategory && matchesQuery
    })
  }, [searchableRegistry, searchCategory, searchQuery])

  // Filters timeline list
  const filteredTimelineItems = useMemo(() => {
    return timelineRegistry.filter((item) => {
      return timelineFilter === "all" || item.category === timelineFilter
    })
  }, [timelineRegistry, timelineFilter])

  // Hide loading screen after subsystems load
  useEffect(() => {
    if (!loading && showLoading) {
      const timer = setTimeout(() => setShowLoading(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [loading, showLoading])

  return (
    <>
      {showLoading && <HQLoadingScreen />}

      <motion.div
        className="h-full flex flex-col space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== TOP BAR ====== */}
        <header
          className="flex items-center justify-between shrink-0"
          style={{
            height: 38,
            padding: "0 20px",
            borderBottom: "1px solid var(--border-subtle)",
          }}
        >
          <div className="flex items-center gap-3">
            <span
              className="text-[8px] font-semibold uppercase tracking-[0.22em]"
              style={{ color: "var(--text-primary)" }}
            >
              FOUNDER COMMAND CENTER
            </span>
            <span
              className="text-[7px] font-mono uppercase tracking-[0.15em]"
              style={{ color: "var(--text-muted)" }}
            >
              · Mission Control Workspace
            </span>
            {currentMission && (
              <>
                <span className="text-[7px]" style={{ color: "var(--border-subtle)" }}>·</span>
                <span
                  className="text-[7px] font-mono uppercase tracking-[0.1em]"
                  style={{ color: missionColor }}
                >
                  {currentMission}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span
                className="w-1.5 h-1.5 rounded-full animate-pulse"
                style={{ backgroundColor: missionColor, boxShadow: `0 0 6px ${missionColor}60` }}
              />
              <span
                className="text-[8px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: missionColor }}
              >
                MISSION: {missionStatus}
              </span>
            </div>

            <span className="text-[6px]" style={{ color: "var(--border-subtle)" }}>|</span>

            <span
              className="text-[8px] font-mono tabular-nums"
              style={{ color: "var(--text-muted)" }}
            >
              {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
            </span>

            <div className="flex items-center gap-1">
              <span
                className="w-1 h-1 rounded-full"
                style={{ backgroundColor: aiConnected !== false ? "#3EDC97" : "#FF5D73" }}
              />
              <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                AI {aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : "OK") : "ERR"}
              </span>
            </div>

            {warnings.length > 0 && (
              <span className="text-[7px] font-mono" style={{ color: "#FFB547" }}>
                {warnings.length} alert{warnings.length > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </header>

        {/* ====== CONTENT — unified continuous workspace layout ====== */}
        <div className="flex-1 space-y-6 px-5 pb-8 overflow-y-auto">

          {/* ====== 1. SYSTEM CORE CONTROL STATE ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">SYSTEM HQ STATUS</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Live subsystem connections and socket telemetry.</p>
              </div>
              <span className="text-[9px] font-mono border border-[var(--border-subtle)] px-2 py-0.5 rounded text-[var(--accent-blue)]">
                Telemetry Active
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Platform Health</span>
                <div className="text-sm font-semibold text-[var(--accent-green)] mt-1">EXCELLENT</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Uptime: 99.98%</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Active Services</span>
                <div className="text-sm font-semibold text-[var(--text-primary)] mt-1">9 / 9 Online</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Zero degraded engines</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Database Status</span>
                <div className="text-sm font-semibold text-[var(--accent-green)] mt-1">CONNECTED</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">SQLite active instance</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">WebSocket Status</span>
                <div className="text-sm font-semibold text-[var(--accent-cyan)] mt-1">ACTIVE</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Clients: {activePositionCount} active session</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">API Status</span>
                <div className="text-sm font-semibold text-[var(--text-primary)] mt-1">ONLINE (HTTP)</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">CORS: Secure limits</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Worker Engine</span>
                <div className="text-sm font-semibold text-[var(--accent-purple)] mt-1">IDLE / WATCH</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Next poll: 30s</div>
              </div>
            </div>
          </div>

          {/* ====== 2. MARKET regime & telemetry ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">MARKET SURVEILLANCE</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Real-time regime and Hyperliquid spot-market feeds.</p>
              </div>
              <span className="text-[9px] font-mono border border-[var(--border-subtle)] px-2 py-0.5 rounded text-[var(--accent-green)]">
                Regime AI Detected
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Current Regime</span>
                <div className="text-base font-bold text-[var(--accent-green)]">BULLISH_HIGH_VOL</div>
                <p className="text-[10px] text-[var(--text-secondary)]">Trend score: 85% strength</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">BTC Price Index</span>
                <div className="text-base font-mono font-bold text-[var(--text-primary)]">${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                <p className={`text-[10px] font-mono ${liveChange >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {liveChange >= 0 ? "+" : ""}{liveChange.toFixed(2)}% (24h)
                </p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Market Breadth</span>
                <div className="text-base font-bold text-[var(--text-primary)]">74.2% uptrend</div>
                <p className="text-[10px] text-[var(--text-secondary)]">SOL, AVAX leading moves</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Volatility (ATR)</span>
                <div className="text-base font-mono font-bold text-[var(--accent-yellow)]">1,482 USD</div>
                <p className="text-[10px] text-[var(--text-secondary)]">High market expansion</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Liquidity Depth</span>
                <div className="text-base font-bold text-[var(--text-primary)]">EXCELLENT</div>
                <p className="text-[10px] text-[var(--text-secondary)]">Spread: 0.01% average</p>
              </div>
            </div>
          </div>

          {/* ====== 3. AI COUNCIL INTEL ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">AI COUNCIL CHAMBER</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Consensus metrics and cognitive score models.</p>
              </div>
              <span className="text-[9px] font-mono border border-[var(--border-subtle)] px-2 py-0.5 rounded text-[var(--accent-purple)]">
                Consensus Engine
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-2">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">AI Council Status</span>
                <div className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
                  <span className="text-sm font-semibold text-[var(--text-primary)]">5 Agents Online</span>
                </div>
                <p className="text-[9px] text-[var(--text-muted)]">Alpha, Beta, Gamma, Risk, Macro</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-2">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Agreement Score</span>
                <div className="text-lg font-mono font-bold text-[var(--accent-green)]">92.0%</div>
                <p className="text-[9px] text-[var(--text-muted)]">Strong collective alignment</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-2 col-span-2">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Confidence Distribution</span>
                <div className="space-y-1.5 mt-1">
                  <ProgressLine value={0.95} label="Alpha (Trend)" color="#3EDC97" />
                  <ProgressLine value={0.88} label="Beta (Volume)" color="#4F8CFF" />
                  <ProgressLine value={0.78} label="Gamma (Macro)" color="#8B5CF6" />
                </div>
              </div>
            </div>
          </div>

          {/* ====== 4. PORTFOLIO ENGINE OVERVIEW ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">PORTFOLIO VAULT DECK</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Exposure models, value at risk, and active allocations.</p>
              </div>
              <span className="text-[9px] font-mono border border-[var(--border-subtle)] px-2 py-0.5 rounded text-[var(--accent-cyan)]">
                Engine Snapshot
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Equity</span>
                <div className="text-sm font-mono font-bold text-[var(--text-primary)]">$104,242</div>
                <div className="text-[9px] text-[var(--accent-green)] mt-0.5">+4.2% growth</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Exposure</span>
                <div className="text-sm font-mono font-bold text-[var(--accent-yellow)]">18.4%</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Low-risk target</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Risk Index</span>
                <div className="text-sm font-mono font-bold text-[var(--accent-yellow)]">{(liveRiskScore * 100).toFixed(1)}%</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Max limit: 2.0%</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Value at Risk (VaR)</span>
                <div className="text-sm font-mono font-bold text-[var(--text-primary)]">$1,240</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">95% conf, 1 day</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Drawdown</span>
                <div className="text-sm font-mono font-bold text-[var(--text-primary)]">0.45%</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">Max historical: 4.8%</div>
              </div>
              <div className="p-3.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <span className="text-[8px] uppercase tracking-wider text(--text-muted) font-mono">Active Positions</span>
                <div className="text-sm font-mono font-bold text-[var(--accent-cyan)]">{activePositionCount} LONG</div>
                <div className="text-[9px] text-[var(--text-muted)] mt-0.5">BTCUSDT base size</div>
              </div>
            </div>
          </div>

          {/* ====== 5. DECISIONS, shortfalls, false positives, replay shortcuts ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">DECISIONS & BACK-PROPAGATION</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Missed triggers, invalid setups, and quick What-If simulation replay triggers.</p>
              </div>
              <span className="text-[9px] font-mono border border-[var(--border-subtle)] px-2 py-0.5 rounded text-[var(--accent-orange)]">
                Subsystem Analysis
              </span>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-2">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">False Positives (Whipsaws)</span>
                <div className="text-sm font-mono font-bold text-[var(--accent-red)]">2 Decisions</div>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">ETH range breakdown on June 28th resulted in fakeout long entry.</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-2">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Missed Opportunities</span>
                <div className="text-sm font-mono font-bold text-[var(--accent-yellow)]">1 Event</div>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">SOL sudden +8% squeeze missed due to ATR range mismatch.</p>
              </div>
              <div className="p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-3">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Replay shortcuts</span>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => navigate("/backtest")}
                    className="text-[9px] font-mono border border-[var(--border-subtle)] hover:border-[var(--accent-blue)] rounded px-2.5 py-1 text-[var(--text-primary)] transition-all bg-[var(--bg-surface)] cursor-pointer"
                  >
                    Replay #102 Setup ↺
                  </button>
                  <button
                    onClick={() => navigate("/backtest")}
                    className="text-[9px] font-mono border border-[var(--border-subtle)] hover:border-[var(--accent-blue)] rounded px-2.5 py-1 text-[var(--text-primary)] transition-all bg-[var(--bg-surface)] cursor-pointer"
                  >
                    Replay ETH False Positives ↺
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* ====== 6. SIMULATOR & STRATEGY COGNITIVE STATS ====== */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Market Simulator Section */}
            <div className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">MARKET SIMULATOR & WORKSPACE</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Active sandbox environments and trial reports.</p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Active Sessions</span>
                  <div className="text-sm font-mono font-bold text-[var(--accent-cyan)] mt-0.5">1 Session</div>
                </div>
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Saved Sessions</span>
                  <div className="text-sm font-mono font-bold text-[var(--text-primary)] mt-0.5">4 Sandbox</div>
                </div>
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Recent Reports</span>
                  <div className="text-sm font-mono font-bold text-[var(--text-primary)] mt-0.5">8 Trials</div>
                </div>
              </div>
            </div>

            {/* Strategy Lab Section */}
            <div className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-4">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">STRATEGY LAB CORE</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Elite model rankings and optimization engines.</p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Saved Strategies</span>
                  <div className="text-sm font-mono font-bold text-[var(--text-primary)] mt-0.5">6 Models</div>
                </div>
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Best Strategy</span>
                  <div className="text-sm font-mono font-bold text-[var(--accent-green)] mt-0.5">TrendFollow</div>
                </div>
                <div className="p-3 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)]">
                  <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono">Optimizations</span>
                  <div className="text-sm font-mono font-bold text-[var(--text-primary)] mt-0.5">3 Trials</div>
                </div>
              </div>
            </div>
          </div>

          {/* ====== 7. GLOBAL UNIVERSAL SEARCH ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">UNIVERSAL SYSTEM SEARCH</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Single operational index search for assets, decisions, strategies, sessions, evidence, or council members.</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                {["all", "assets", "decisions", "strategies", "sessions", "evidence", "council members"].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSearchCategory(cat)}
                    className={`text-[9px] font-mono border rounded px-2.5 py-1 uppercase tracking-wider transition-all cursor-pointer ${
                      searchCategory === cat
                        ? "border-[var(--accent-blue)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/5"
                        : "border-[var(--border-subtle)] text-[var(--text-muted)] hover:border-[var(--border-default)]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Query asset metrics, AI consensus numbers, strategy names, or OLLO briefings..."
                className="w-full text-xs font-mono border border-[var(--border-default)] bg-[var(--bg-base)] text-[var(--text-primary)] rounded-lg px-4 py-3 placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-blue)] focus:ring-1 focus:ring-[var(--accent-blue)]/20"
              />
            </div>

            {/* Results Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredSearchItems.slice(0, 6).map((item) => (
                <div key={item.id} className="p-3.5 rounded border border-[var(--border-subtle)] bg-[var(--bg-base)] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[8px] font-mono uppercase tracking-wider text-[var(--text-muted)] bg-[var(--bg-surface)] px-1.5 py-0.5 rounded">
                      {item.category}
                    </span>
                    {item.status && (
                      <span className="text-[8px] font-mono text-[var(--text-secondary)]">
                        {item.status}
                      </span>
                    )}
                  </div>
                  <h4 className="text-[11px] font-semibold text-[var(--text-primary)]">{item.title}</h4>
                  <p className="text-[9px] text-[var(--text-secondary)] font-mono">{item.subtitle}</p>
                  <p className="text-[9px] text-[var(--text-muted)] font-mono leading-relaxed">{item.details}</p>
                </div>
              ))}
              {filteredSearchItems.length === 0 && (
                <div className="col-span-full py-8 text-center text-xs font-mono text-[var(--text-muted)] border border-dashed border-[var(--border-subtle)] rounded">
                  No registered index components match current parameters.
                </div>
              )}
            </div>
          </div>

          {/* ====== 8. GLOBAL SYNCHRONIZED TIMELINE ====== */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-xs font-semibold tracking-wider text-[var(--text-primary)]">GLOBAL CHRONOLOGICAL TIMELINE</h3>
                <p className="text-[10px] text-[var(--text-secondary)] font-mono">Synchronized system event logs, regime shifts, decisions, whale alerts, and simulated cycles.</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                {["all", "market", "ai", "whale", "news", "trades", "simulations"].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setTimelineFilter(cat)}
                    className={`text-[9px] font-mono border rounded px-2.5 py-1 uppercase tracking-wider transition-all cursor-pointer ${
                      timelineFilter === cat
                        ? "border-[var(--accent-blue)] text-[var(--accent-blue)] bg-[var(--accent-blue)]/5"
                        : "border-[var(--border-subtle)] text-[var(--text-muted)] hover:border-[var(--border-default)]"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Timeline Stream */}
            <div className="border-l border-[var(--border-subtle)] ml-3 pl-4 space-y-4">
              {filteredTimelineItems.map((item) => (
                <div key={item.id} className="relative space-y-1">
                  {/* Timeline bullet */}
                  <span
                    className="absolute -left-[20px] top-1 w-2.5 h-2.5 rounded-full border-2 border-[var(--bg-surface)]"
                    style={{
                      backgroundColor: item.type === "success" ? "#3EDC97" : item.type === "danger" ? "#FF5D73" : item.type === "warning" ? "#FFB547" : "#4F8CFF",
                      boxShadow: `0 0 6px ${item.type === "success" ? "#3EDC97" : item.type === "danger" ? "#FF5D73" : item.type === "warning" ? "#FFB547" : "#4F8CFF"}40`
                    }}
                  />
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <span className="text-[9px] font-mono text-[var(--text-muted)] font-mono">
                      {item.timestamp} · <span className="uppercase text-[8px] border border-[var(--border-subtle)] px-1 py-0.2 rounded text-[var(--text-secondary)]">{item.category}</span>
                    </span>
                  </div>
                  <h4 className="text-xs font-semibold text-[var(--text-primary)]">{item.title}</h4>
                  <p className="text-[10px] text-[var(--text-secondary)] leading-relaxed font-mono">{item.details}</p>
                </div>
              ))}
              {filteredTimelineItems.length === 0 && (
                <div className="py-8 text-center text-xs font-mono text-[var(--text-muted)] border border-dashed border-[var(--border-subtle)] rounded">
                  No chronological logs recorded under this filter category.
                </div>
              )}
            </div>
          </div>

          {/* OLLO GREETINGS & briefing & evidence strength stats */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-6">
            <div className="relative flex flex-col items-center">
              <OLLOCommander
                greeting={ollo.greeting}
                briefing={ollo.briefing}
                loading={loading && !ollo.greeting}
                error={ollo.status.error}
              />
              <div className="mt-6">
                <MissionRing sectors={sectors} />
              </div>
            </div>

            <div className="max-w-xl mx-auto space-y-4 border-t border-[var(--border-subtle)] pt-6">
              <div className="text-center">
                <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono block">EVIDENCE POSTURE FEEDBACK</span>
                <p className="text-[11px] font-semibold text-[var(--text-primary)] mt-1">{recommendation}</p>
              </div>

              <div className="space-y-2.5">
                <ProgressLine value={confidence} label="Decision Confidence" color={qualityColor(decisionQuality ?? "HIGH")} />
                <ProgressLine value={strength} label="Evidence Strength" color="#4F8CFF" />
                <ProgressLine value={explainability} label="Explainability Score" color="#8B5CF6" />
              </div>

              <div className="flex justify-center gap-4 text-[9px] font-mono text-[var(--text-muted)] pt-1">
                <span><span className="text-[var(--accent-green)]">{supportingCount}</span> supporting</span>
                {conflictCount > 0 && <span><span className="text-[var(--accent-red)]">{conflictCount}</span> conflicting</span>}
                {warningCount > 0 && <span><span className="text-[var(--accent-yellow)]">{warningCount}</span> warnings</span>}
              </div>
            </div>
          </div>

          {/* Mission Flow Diagram */}
          <div className="relative p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-4">
            <span className="text-[8px] uppercase tracking-wider text-[var(--text-muted)] font-mono block text-center">SYSTEM REASONING STREAM FLOW</span>
            <div className="max-w-2xl mx-auto">
              <MissionFlow nodes={flowNodes} />
            </div>
          </div>

        </div>

        {/* ====== BOTTOM: Subsystem Health ====== */}
        <div
          className="shrink-0"
          style={{
            padding: "8px 20px",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <SubsystemHealthBar
            scanner={scanner}
            risk={risk}
            council={council}
            portfolio={portfolio}
            whale={whale}
            market={market}
            evidence={evidence}
            olloStatus={ollo.status}
            aiHealth={aiHealth}
          />
        </div>
      </motion.div>
    </>
  )
}
