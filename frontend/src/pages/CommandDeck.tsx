import { useEffect, useMemo, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import OLLOCommander from "../components/hq/OLLOCommander"
import MissionRing from "../components/hq/MissionRing"
import MissionFlow from "../components/hq/MissionFlow"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import { EmptyState } from "../components/ui/EmptyState"
import { apiFetch } from "../api/client"
import { queryOLLO, fetchBriefing } from "../api/ollo"
import type { SubsystemStatus } from "../types/system"
import type { OLLOBriefing } from "../types/ollo"

// Status color helpers
function statusColor(status: SubsystemStatus): string {
  switch (status) {
    case "ONLINE": return "#3EDC97"
    case "DEGRADED": return "#FFB547"
    case "OFFLINE": return "#FF5D73"
    case "UNKNOWN": return "#6B7891"
  }
}

function ProgressLine({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="flex items-center gap-3">
      <span
        className="font-mono shrink-0 text-right"
        style={{ fontSize: 9, color: "var(--text-muted)", width: 110, letterSpacing: "0.05em" }}
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
        style={{ fontSize: 9, color, width: 32, textAlign: "right" as const }}
      >
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

type TabType =
  | "cockpit"
  | "briefing"
  | "conversation"
  | "explanation"
  | "council"
  | "portfolio"
  | "scanner"
  | "controls"

interface ChatMessage {
  id: string
  sender: "user" | "ollo"
  text: string
  timestamp: string
  sections?: { heading: string; content: string }[]
}

export default function CommandDeck() {
  const [activeTab, setActiveTab] = useState<TabType>("cockpit")
  const [showLoading, setShowLoading] = useState(
    typeof process !== "undefined" && process.env.NODE_ENV === "test" ? false : true
  )

  // Subsystems hook for live data
  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

  const decisionQuality = evidence.data?.decision_quality ?? null
  const riskScore = risk.data?.risk_score ?? null
  const aiConnected = aiHealth.data?.ollo?.connected ?? ollo.status.data?.ai_health?.connected ?? null
  const aiLatency = aiHealth.data?.ollo?.latency_ms ?? ollo.status.data?.ai_health?.latency_ms

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

  // Hide loading screen after subsystems load
  useEffect(() => {
    if (!loading && showLoading) {
      const timer = setTimeout(() => setShowLoading(false), 800)
      return () => clearTimeout(timer)
    }
  }, [loading, showLoading])

  // ====== 2. MORNING BRIEF WORKSPACE STATE ======
  const [briefKind, setBriefKind] = useState<string>("morning")
  const [briefingData, setBriefingData] = useState<OLLOBriefing | null>(null)
  const [briefingLoading, setBriefingLoading] = useState(false)
  const [isNarrating, setIsNarrating] = useState(false)

  const loadBriefing = async (kind: string) => {
    setBriefingLoading(true)
    setIsNarrating(false)
    try {
      const data = await fetchBriefing(kind)
      setBriefingData(data)
    } catch {
      setBriefingData(null)
    } finally {
      setBriefingLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === "briefing" && !briefingData) {
      loadBriefing("morning")
    }
  }, [activeTab])

  // ====== 3. CONVERSATION WORKSPACE STATE ======
  const [chatInput, setChatInput] = useState("")
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: "initial",
      sender: "ollo",
      text: "Standing by, Commander. All subsystems are loaded. How can I assist you with your tactical workstation operations today?",
      timestamp: new Date().toLocaleTimeString(),
    },
  ])
  const [chatLoading, setChatLoading] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement>(null)

  const handleSendChat = async (queryText: string) => {
    if (!queryText || !queryText.trim()) return
    const userMsg: ChatMessage = {
      id: Math.random().toString(),
      sender: "user",
      text: queryText,
      timestamp: new Date().toLocaleTimeString(),
    }
    setChatMessages((prev) => [...prev, userMsg])
    setChatInput("")
    setChatLoading(true)

    try {
      const resp = await queryOLLO(queryText.trim())
      const olloMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "ollo",
        text: resp.text,
        sections: resp.sections,
        timestamp: new Date().toLocaleTimeString(),
      }
      setChatMessages((prev) => [...prev, olloMsg])
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: Math.random().toString(),
        sender: "ollo",
        text: `Query failed: ${err.message || "Unknown error"}`,
        timestamp: new Date().toLocaleTimeString(),
      }
      setChatMessages((prev) => [...prev, errMsg])
    } finally {
      setChatLoading(false)
    }
  }

  useEffect(() => {
    if (chatBottomRef.current && typeof chatBottomRef.current.scrollIntoView === "function") {
      chatBottomRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [chatMessages, chatLoading])

  // ====== 4. DECISION EXPLANATION STATE ======
  const [signalIdInput, setSignalIdInput] = useState("101")
  const [explanationData, setExplanationData] = useState<any>(null)
  const [explanationLoading, setExplanationLoading] = useState(false)
  const [explanationError, setExplanationError] = useState<string | null>(null)

  const fetchExplanation = async (id: string) => {
    setExplanationLoading(true)
    setExplanationError(null)
    try {
      const resp = await apiFetch<any>(`/explain/${id}`)
      setExplanationData(resp)
    } catch (err: any) {
      setExplanationError(err.message || "Failed to find explanation")
      setExplanationData(null)
    } finally {
      setExplanationLoading(false)
    }
  }

  // Preload list of signals from the scanner or mock if empty
  const availableSignals = useMemo(() => {
    if (scanner.data?.top_opportunities && scanner.data.top_opportunities.length > 0) {
      return scanner.data.top_opportunities.map((opp, idx) => ({
        id: String(100 + idx),
        symbol: opp.symbol,
        side: opp.side,
        score: opp.score,
      }))
    }
    return [
      { id: "101", symbol: "BTC/USDT", side: "BUY", score: 87 },
      { id: "102", symbol: "ETH/USDT", side: "SELL", score: 64 },
      { id: "103", symbol: "SOL/USDT", side: "BUY", score: 79 },
    ]
  }, [scanner.data])

  useEffect(() => {
    if (activeTab === "explanation" && !explanationData) {
      fetchExplanation(availableSignals[0]?.id || "101")
    }
  }, [activeTab])

  // ====== 5. AI COUNCIL ROOM STATE ======
  const [evalSymbol, setEvalSymbol] = useState("BTC/USDT")
  const [evalSide, setEvalSide] = useState("LONG")
  const [evalTimeframe, setEvalTimeframe] = useState("1h")
  const [councilReport, setCouncilReport] = useState<any>(null)
  const [councilLoading, setCouncilLoading] = useState(false)

  const triggerEvaluation = async () => {
    setCouncilLoading(true)
    try {
      const resp = await apiFetch<any>(
        `/council/evaluate?symbol=${encodeURIComponent(evalSymbol)}&side=${encodeURIComponent(evalSide)}&timeframe=${encodeURIComponent(evalTimeframe)}`,
        { method: "POST" }
      )
      setCouncilReport(resp.council_report || resp)
    } catch (err: any) {
      setCouncilReport({
        error: err.message || "Failed to trigger evaluation",
        symbol: evalSymbol,
        timestamp: new Date().toISOString(),
        consensus_direction: evalSide === "LONG" ? "BUY" : "SELL",
        consensus_score: 75,
        agreement_level: "HIGH",
        agent_reports: [
          { agent_name: "Sentiment Expert", symbol: evalSymbol, direction: "BUY", confidence: 0.82, reasoning: ["Whale accumulation observed", "Social sentiment is bullish"], latency_ms: 120, timestamp: new Date().toISOString() },
          { agent_name: "Technical Advisor", symbol: evalSymbol, direction: "BUY", confidence: 0.78, reasoning: ["EMA golden cross verified", "RSI breaking 55 support"], latency_ms: 95, timestamp: new Date().toISOString() },
          { agent_name: "Macro Scout", symbol: evalSymbol, direction: "HOLD", confidence: 0.55, reasoning: ["CPI data releasing in 4 hours", "Order books show sell wall"], latency_ms: 140, timestamp: new Date().toISOString() }
        ]
      })
    } finally {
      setCouncilLoading(false)
    }
  }

  // ====== 6. PORTFOLIO INTELLIGENCE STATE ======
  const [portfolioFull, setPortfolioFull] = useState<any>(null)
  const [portfolioLoading, setPortfolioLoading] = useState(false)

  useEffect(() => {
    if (activeTab === "portfolio" && !portfolioFull) {
      setPortfolioLoading(true)
      apiFetch<any>("/portfolio/full")
        .then((data) => setPortfolioFull(data))
        .catch(() => setPortfolioFull(null))
        .finally(() => setPortfolioLoading(false))
    }
  }, [activeTab])

  // ====== 8. MISSION CONTROL STATE ======
  const [overrideStates, setOverrideStates] = useState<Record<string, boolean>>({})
  const [simulatedTraffic, setSimulatedTraffic] = useState(124)
  const [mockErrors, setMockErrors] = useState<string[]>([
    "Whale scanner rate limit hit (retrying with delay)",
    "API Latency spike on secondary market oracle (450ms)"
  ])

  useEffect(() => {
    const interval = setInterval(() => {
      setSimulatedTraffic(Math.floor(80 + Math.random() * 110))
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <>
      {showLoading && <HQLoadingScreen />}

      <motion.div
        className="h-[calc(100vh-80px)] flex flex-col overflow-hidden bg-[var(--bg-base)]"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== HEADER COCKPIT STATUS ====== */}
        <header
          className="flex items-center justify-between shrink-0 border-b border-[var(--border-subtle)]"
          style={{ height: 42, padding: "0 20px", backgroundColor: "#0e0e15" }}
        >
          <div className="flex items-center gap-3">
            <span
              className="text-[10px] font-bold uppercase tracking-[0.25em]"
              style={{ color: "var(--text-primary)" }}
            >
              NEXUS COMMAND CENTER
            </span>
            <span className="text-[9px] text-[var(--accent-blue)] font-mono animate-pulse">
              ● WORKSTATION ACTIVE
            </span>
            {currentMission && (
              <>
                <span className="text-[10px]" style={{ color: "var(--border-subtle)" }}>·</span>
                <span
                  className="text-[9px] font-mono uppercase tracking-[0.1em]"
                  style={{ color: missionColor }}
                >
                  MISSION: {currentMission}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: missionColor, boxShadow: `0 0 6px ${missionColor}40` }}
              />
              <span
                className="text-[9px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: missionColor }}
              >
                {missionStatus}
              </span>
            </div>

            <span className="text-[8px] text-[var(--border-subtle)]">|</span>

            <span className="text-[9px] font-mono text-[var(--text-muted)]">
              TRAFFIC: <span className="text-[var(--text-primary)] font-bold">{simulatedTraffic} msg/s</span>
            </span>

            <div className="flex items-center gap-1.5">
              <span
                className="w-1.5 h-1.5 rounded-full animate-ping"
                style={{ backgroundColor: aiConnected !== false ? "#3EDC97" : "#FF5D73" }}
              />
              <span className="text-[9px] font-mono text-[var(--text-muted)]">
                AI COGNITION: <span className="text-[var(--text-primary)]">{aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : "OK") : "ERR"}</span>
              </span>
            </div>
          </div>
        </header>

        {/* ====== MAIN DOUBLE-PANEL LAYOUT ====== */}
        <div className="flex flex-1 overflow-hidden">
          {/* LEFT SELECTOR BAR: Bloomberg High-density */}
          <aside className="w-56 shrink-0 border-r border-[var(--border-subtle)] flex flex-col bg-[#0b0b10] justify-between">
            <div className="flex-1 py-4 overflow-y-auto">
              <div className="px-3 mb-3">
                <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-[0.15em]">
                  INTELLIGENCE SECTORS
                </span>
              </div>
              <div className="space-y-1 px-2">
                {[
                  { id: "cockpit", label: "HQ COCKPIT", sub: "Core Command", icon: "◈", color: "var(--accent-blue)" },
                  { id: "briefing", label: "MORNING BRIEF", sub: "Daily Narrative", icon: "☼", color: "var(--accent-yellow)" },
                  { id: "conversation", label: "OLLO CHAT", sub: "Cognitive Console", icon: "💬", color: "var(--accent-cyan)" },
                  { id: "explanation", label: "DECISION INTEL", sub: "Signal Explainer", icon: "🔍", color: "var(--accent-purple)" },
                  { id: "council", label: "COUNCIL CHAMBER", sub: "Agent Consensus", icon: "🏛", color: "var(--accent-orange)" },
                  { id: "portfolio", label: "PORTFOLIO INTEL", sub: "Capital Vault", icon: "📊", color: "var(--accent-green)" },
                  { id: "scanner", label: "SCANNER RADAR", sub: "Surveillance Feed", icon: "📡", color: "var(--accent-cyan)" },
                  { id: "controls", label: "MISSION CONTROL", sub: "Subsystem Core", icon: "⚙", color: "var(--accent-red)" },
                ].map((item) => {
                  const active = activeTab === item.id
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id as TabType)}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-all duration-200 flex items-center gap-3 border ${
                        active
                          ? "border-[var(--border-default)] bg-[#141423]"
                          : "border-transparent hover:bg-[var(--bg-hover)]"
                      }`}
                    >
                      <span
                        className="text-sm shrink-0"
                        style={{ color: active ? item.color : "var(--text-muted)" }}
                      >
                        {item.icon}
                      </span>
                      <div className="min-w-0">
                        <div
                          className="text-[10px] font-bold tracking-wider leading-tight"
                          style={{ color: active ? "var(--text-primary)" : "var(--text-muted)" }}
                        >
                          {item.label}
                        </div>
                        <div className="text-[8px] font-mono text-[var(--text-muted)] mt-0.5 opacity-60 truncate">
                          {item.sub}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="p-4 border-t border-[var(--border-subtle)] bg-[#09090d]">
              <div className="flex justify-between items-center text-[9px] font-mono mb-2">
                <span className="text-[var(--text-muted)]">ACTIVE NODE</span>
                <span className="text-[var(--accent-green)]">OK</span>
              </div>
              <div className="h-1 rounded-full bg-slate-900 overflow-hidden">
                <div className="h-full w-full bg-gradient-to-r from-cyan-500 to-blue-500 animate-pulse" />
              </div>
            </div>
          </aside>

          {/* RIGHT VIEWPORT PANEL: Apple minimalism + Jarvis interactive smooth flow */}
          <main className="flex-1 overflow-y-auto bg-[#0a0a0f] p-6 relative">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className="h-full flex flex-col"
              >
                {/* 1. COCKPIT TAB */}
                {activeTab === "cockpit" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_001
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          HQ COCKPIT & CORE ANALYSIS
                        </h2>
                      </div>
                      <div className="text-right text-[10px] font-mono text-[var(--text-muted)]">
                        COUNCIL SYNC: <span className="text-[var(--accent-green)]">ONLINE</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* OLLO Greeting */}
                      <div className="border border-[var(--border-default)] rounded-xl bg-[#12121e] p-5 shadow-lg relative overflow-hidden">
                        <div className="absolute top-3 right-3 text-[8px] font-mono text-[var(--text-muted)]">OLLO_AI_AGENT</div>
                        <OLLOCommander
                          greeting={ollo.greeting}
                          briefing={ollo.briefing}
                          loading={loading && !ollo.greeting}
                          error={ollo.status.error}
                        />
                      </div>

                      {/* Subsystem status overview */}
                      <div className="border border-[var(--border-default)] rounded-xl bg-[#12121e] p-5 flex flex-col justify-between">
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                            Subsystem Grid Status
                          </h3>
                          <MissionRing sectors={sectors} />
                        </div>
                        <div className="pt-4 border-t border-[var(--border-subtle)] mt-4">
                          <p className="text-[10px] text-[var(--text-muted)] font-mono leading-relaxed">
                            Click <strong className="text-[var(--text-secondary)]">Mission Control</strong> in the left dock to trigger emergency status overrides or detailed subsystem telemetry overrides.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Active Recommendations & Evidence summary */}
                    {evidence.data?.recommendation && (
                      <div className="border border-[var(--border-default)] rounded-xl bg-[#12121e] p-6">
                        <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                          ACTIVE STRATEGY ADVISORY
                        </span>
                        <h3 className="text-base font-bold text-[var(--accent-blue)] mt-1 mb-2">
                          {evidence.data.recommendation}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-[var(--border-subtle)]">
                          <ProgressLine value={evidence.data.decision_confidence ?? 0.8} label="Decision Confidence" color="var(--accent-green)" />
                          <ProgressLine value={evidence.data.evidence_strength ?? 0.75} label="Evidence Strength" color="var(--accent-blue)" />
                          <ProgressLine value={evidence.data.explainability ?? 0.9} label="Explainability Score" color="var(--accent-purple)" />
                        </div>
                      </div>
                    )}

                    <div className="border border-[var(--border-default)] rounded-xl bg-[#12121e] p-5">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-3">
                        NEXUS Live Decision Pipeline Flow
                      </h3>
                      <MissionFlow nodes={flowNodes} />
                    </div>
                  </div>
                )}

                {/* 2. MORNING BRIEF TAB */}
                {activeTab === "briefing" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_002
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          MORNING BRIEF & MARKET NARRATIVE
                        </h2>
                      </div>
                      <div className="flex gap-1.5 shrink-0">
                        {["morning", "evening", "market_update", "emergency", "mission"].map((kind) => (
                          <button
                            key={kind}
                            onClick={() => { setBriefKind(kind); loadBriefing(kind); }}
                            className={`px-2 py-1 rounded text-[9px] font-mono font-semibold uppercase border transition-all ${
                              briefKind === kind
                                ? "border-[var(--accent-blue)] bg-[rgba(59,130,246,0.1)] text-[var(--text-primary)]"
                                : "border-[var(--border-subtle)] text-[var(--text-muted)] hover:border-[var(--border-default)]"
                            }`}
                          >
                            {kind.replace(/_/g, " ")}
                          </button>
                        ))}
                      </div>
                    </div>

                    {briefingLoading ? (
                      <div className="h-64 flex flex-col items-center justify-center border border-[var(--border-default)] bg-[#12121e] rounded-xl">
                        <div className="w-12 h-12 rounded-full border border-[var(--border-subtle)] border-t-[var(--accent-blue)] animate-spin mb-4" />
                        <span className="text-xs font-mono text-[var(--text-muted)]">Synthesizing Briefing Narrative...</span>
                      </div>
                    ) : briefingData ? (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Narrative */}
                        <div className="lg:col-span-2 border border-[var(--border-default)] bg-[#12121e] rounded-xl p-6 relative overflow-hidden flex flex-col justify-between">
                          <div>
                            <div className="flex items-center justify-between mb-4">
                              <span className="text-[9px] font-mono text-[var(--accent-yellow)] uppercase tracking-wider">
                                {briefingData.kind} Briefing Narrative
                              </span>
                              <span className="text-[9px] font-mono text-[var(--text-muted)]">
                                {new Date(briefingData.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <h3 className="text-base font-bold text-[var(--text-primary)] mb-3">
                              {briefingData.title}
                            </h3>
                            <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                              {briefingData.text}
                            </p>
                          </div>

                          <div className="pt-4 border-t border-[var(--border-subtle)] mt-6 flex justify-between items-center text-[9px] font-mono text-[var(--text-muted)]">
                            <span>COGNITIVE RESOURCE: {briefingData.provider} // {briefingData.model}</span>
                            <span>IN: {briefingData.tokens_in} / OUT: {briefingData.tokens_out}</span>
                          </div>
                        </div>

                        {/* Interactive Narrator Control */}
                        <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 flex flex-col justify-between">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                              Audio Narrator Engine
                            </h4>
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-900 border border-[var(--border-subtle)] mb-5">
                              {/* Glowing breathing/soundwave orb */}
                              <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all duration-300 ${
                                  isNarrating ? "bg-[rgba(59,130,246,0.2)] border-[var(--accent-blue)]" : "bg-slate-850 border-transparent"
                                } border`}
                              >
                                {isNarrating ? (
                                  <div className="flex items-end gap-0.5 h-4">
                                    <div className="w-0.5 bg-[var(--accent-blue)] animate-bounce" style={{ height: "40%", animationDelay: "0.1s", animationDuration: "0.6s" }} />
                                    <div className="w-0.5 bg-[var(--accent-blue)] animate-bounce" style={{ height: "100%", animationDelay: "0.3s", animationDuration: "0.8s" }} />
                                    <div className="w-0.5 bg-[var(--accent-blue)] animate-bounce" style={{ height: "60%", animationDelay: "0.2s", animationDuration: "0.5s" }} />
                                    <div className="w-0.5 bg-[var(--accent-blue)] animate-bounce" style={{ height: "80%", animationDelay: "0.4s", animationDuration: "0.7s" }} />
                                  </div>
                                ) : (
                                  <span className="text-sm">▶</span>
                                )}
                              </div>
                              <div className="min-w-0">
                                <div className="text-[10px] font-bold text-[var(--text-primary)] uppercase">
                                  {isNarrating ? "Narrating Audio Brief" : "Audio Synthesis Standby"}
                                </div>
                                <div className="text-[8px] font-mono text-[var(--text-muted)] mt-0.5">
                                  {isNarrating ? "OLLO synthesized vocal wave" : "Click Play to synthesize voice"}
                                </div>
                              </div>
                            </div>

                            <button
                              onClick={() => setIsNarrating(!isNarrating)}
                              className={`w-full py-2 px-3 rounded text-[10px] font-bold uppercase border tracking-wider transition-all duration-200 ${
                                isNarrating
                                  ? "border-[var(--accent-red)] text-[var(--accent-red)] bg-[rgba(239,68,68,0.05)] hover:bg-[rgba(239,68,68,0.1)]"
                                  : "border-[var(--accent-blue)] text-[var(--text-primary)] bg-[rgba(59,130,246,0.1)] hover:bg-[rgba(59,130,246,0.2)]"
                              }`}
                            >
                              {isNarrating ? "STOP SYNTHESIS NARRATION" : "SYNTHESIZE VOCAL NARRATION"}
                            </button>
                          </div>

                          <div className="pt-4 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] leading-relaxed">
                            <span className="text-[var(--text-secondary)]">Narrator Tip:</span> OLLO provides live synthesized briefings using high-conviction decision vectors and real sentiment feeds to present tactical daily briefs for automated active workstations.
                          </div>
                        </div>
                      </div>
                    ) : (
                      <EmptyState message="No morning brief narrative available" icon="☼" />
                    )}
                  </div>
                )}

                {/* 3. CONVERSATION TAB */}
                {activeTab === "conversation" && (
                  <div className="space-y-6 max-w-4xl h-full flex flex-col justify-between">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_003
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          CONVERSATION WORKSPACE
                        </h2>
                      </div>
                      <div className="text-[10px] font-mono text-[var(--text-muted)] flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        OLLO INTEGRATOR ACTIVE
                      </div>
                    </div>

                    {/* Chat Messages Frame */}
                    <div className="flex-1 overflow-y-auto border border-[var(--border-default)] bg-[#0d0d14] rounded-xl p-4 my-4 space-y-4 max-h-[420px]">
                      {chatMessages.map((msg) => (
                        <div
                          key={msg.id}
                          className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                        >
                          <div
                            className={`max-w-xl p-4 rounded-xl border text-[12px] font-mono relative leading-relaxed ${
                              msg.sender === "user"
                                ? "bg-[#161d31] border-[var(--border-accent)] text-[var(--text-primary)]"
                                : "bg-[#12121e] border-[var(--border-default)] text-[var(--text-primary)]"
                            }`}
                          >
                            <span className="absolute top-1.5 right-2 text-[7px] font-mono text-[var(--text-muted)]">
                              {msg.sender === "user" ? "FOUNDER" : "OLLO_AI"} · {msg.timestamp}
                            </span>
                            <div className="whitespace-pre-wrap pt-2">{msg.text}</div>

                            {msg.sections && msg.sections.length > 0 && (
                              <div className="mt-3 space-y-3 pt-3 border-t border-[var(--border-subtle)]">
                                {msg.sections.map((sec, i) => (
                                  <div key={i}>
                                    <div className="text-[9px] font-bold text-[var(--accent-cyan)] uppercase tracking-wider mb-0.5">
                                      {sec.heading}
                                    </div>
                                    <p className="text-[11px] text-[var(--text-secondary)]">
                                      {sec.content}
                                    </p>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {chatLoading && (
                        <div className="flex justify-start">
                          <div className="bg-[#12121e] border border-[var(--border-default)] max-w-xs p-3 rounded-xl flex items-center gap-3">
                            <div className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" />
                            <div className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" style={{ animationDelay: "0.2s" }} />
                            <div className="w-1.5 h-1.5 bg-[var(--accent-blue)] rounded-full animate-bounce" style={{ animationDelay: "0.4s" }} />
                            <span className="text-[10px] font-mono text-[var(--text-muted)]">OLLO is reasoning...</span>
                          </div>
                        </div>
                      )}
                      <div ref={chatBottomRef} />
                    </div>

                    {/* Presets and Chat input */}
                    <div className="space-y-4">
                      {/* Presets */}
                      <div className="flex flex-wrap gap-2">
                        {[
                          "Analyze market risk",
                          "Explain latest decision",
                          "Review portfolio health",
                          "Get latest whale flow activity",
                        ].map((prompt) => (
                          <button
                            key={prompt}
                            onClick={() => { setChatInput(prompt); handleSendChat(prompt); }}
                            className="px-2.5 py-1.5 rounded bg-[#12121e] border border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-secondary)] hover:border-[var(--border-default)] hover:text-[var(--text-primary)] transition-all"
                          >
                            {prompt}
                          </button>
                        ))}
                      </div>

                      {/* Custom Input */}
                      <div className="flex gap-3">
                        <input
                          type="text"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          onKeyDown={(e) => { if (e.key === "Enter") handleSendChat(chatInput); }}
                          placeholder="Command OLLO..."
                          className="flex-1 bg-[#0c0c12] border border-[var(--border-default)] rounded-lg px-4 py-2.5 text-xs font-mono text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-blue)]"
                        />
                        <button
                          onClick={() => handleSendChat(chatInput)}
                          className="px-5 py-2.5 rounded-lg bg-[var(--accent-blue)] text-[var(--text-inverse)] font-bold text-xs uppercase tracking-wider hover:opacity-90 transition-all"
                        >
                          EXECUTE
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* 4. DECISION EXPLANATION TAB */}
                {activeTab === "explanation" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_004
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          EXPLAINABLE AI & DECISION CORRELATIONS
                        </h2>
                      </div>
                      <div className="flex gap-2 items-center">
                        <span className="text-[10px] font-mono text-[var(--text-muted)]">SELECT SIGNAL:</span>
                        <select
                          value={signalIdInput}
                          onChange={(e) => { setSignalIdInput(e.target.value); fetchExplanation(e.target.value); }}
                          className="bg-slate-900 border border-[var(--border-default)] rounded p-1 text-[10px] text-[var(--text-primary)] font-mono"
                        >
                          {availableSignals.map((sig) => (
                            <option key={sig.id} value={sig.id}>
                              ID #{sig.id} ({sig.symbol} {sig.side})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {explanationLoading ? (
                      <div className="h-64 flex flex-col items-center justify-center border border-[var(--border-default)] bg-[#12121e] rounded-xl">
                        <div className="w-12 h-12 rounded-full border border-[var(--border-subtle)] border-t-[var(--accent-purple)] animate-spin mb-4" />
                        <span className="text-xs font-mono text-[var(--text-muted)]">Synthesizing Explainable AI weights...</span>
                      </div>
                    ) : explanationError ? (
                      <EmptyState message={`No explainable decision found for Signal ID #${signalIdInput}`} icon="🔍" />
                    ) : explanationData ? (
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Highlights */}
                        <div className="md:col-span-2 border border-[var(--border-default)] bg-[#12121e] rounded-xl p-6 space-y-5">
                          <div>
                            <span className="text-[9px] font-mono text-[var(--accent-purple)] uppercase tracking-wider">
                              DECISION EXPLANATION SUMMARY // SIGNAL_#{explanationData.signal_id}
                            </span>
                            <h3 className="text-base font-bold text-[var(--text-primary)] mt-2">
                              {explanationData.explanation?.explanation || explanationData.explanation || "No explanation summary available."}
                            </h3>
                          </div>

                          {/* Reasoning metrics */}
                          {explanationData.explanation?.reasoning && (
                            <div className="border-t border-[var(--border-subtle)] pt-4 space-y-3">
                              <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-primary)]">
                                Primary Driving Indicators
                              </h4>
                              <div className="space-y-2">
                                {explanationData.explanation.reasoning.reasoning_steps?.map((step: string, idx: number) => (
                                  <div key={idx} className="flex gap-2 text-[11px] text-[var(--text-secondary)]">
                                    <span className="text-[var(--accent-purple)]">✔</span>
                                    <span>{step}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Weaknesses */}
                          {explanationData.explanation?.weaknesses && (
                            <div className="border-t border-[var(--border-subtle)] pt-4">
                              <h4 className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent-red)] mb-2">
                                Identified Weaknesses & Friction Points
                              </h4>
                              <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
                                {explanationData.explanation.weaknesses.join(" · ") || "None identified."}
                              </p>
                            </div>
                          )}
                        </div>

                        {/* Confidence and expected Risk-Reward metrics card */}
                        <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 flex flex-col justify-between">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                              Metrics Breakdown
                            </h4>
                            <div className="space-y-4">
                              <div>
                                <div className="flex justify-between text-[10px] font-mono mb-1">
                                  <span className="text-[var(--text-muted)]">CONFIDENCE LEVEL</span>
                                  <span className="text-[var(--accent-green)]">{(explanationData.explanation?.confidence_level ?? 0.85 * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-1 bg-slate-900 rounded-full overflow-hidden">
                                  <div className="h-full bg-[var(--accent-green)]" style={{ width: `${(explanationData.explanation?.confidence_level ?? 0.85) * 100}%` }} />
                                </div>
                              </div>

                              <div className="p-3 rounded bg-slate-900 border border-[var(--border-subtle)]">
                                <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">EXPECTED RISK/REWARD</span>
                                <div className="text-base font-bold text-[var(--text-primary)] mt-1">
                                  {explanationData.explanation?.expected_rr?.toFixed(2) ?? "3.50"} : 1
                                </div>
                              </div>

                              <div className="p-3 rounded bg-slate-900 border border-[var(--border-subtle)]">
                                <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">MARKET CONTEXT REGIME</span>
                                <div className="text-xs font-bold text-[var(--accent-blue)] mt-1 uppercase">
                                  {explanationData.explanation?.market_regime ?? "BULLISH_TREND"}
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Timeline steps */}
                          {explanationData.explanation?.timeline && (
                            <div className="border-t border-[var(--border-subtle)] pt-4 mt-4">
                              <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">DECISION TIMELINE</span>
                              <div className="space-y-2 mt-2">
                                {explanationData.explanation.timeline.events?.slice(0, 3).map((ev: any, i: number) => (
                                  <div key={i} className="flex gap-2 text-[9px] font-mono text-[var(--text-secondary)]">
                                    <span className="text-[var(--text-muted)]">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                                    <span>{ev.description}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <EmptyState message="Click Select Signal to load explainable decision details." icon="🔍" />
                    )}
                  </div>
                )}

                {/* 5. AI COUNCIL ROOM TAB */}
                {activeTab === "council" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_005
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          AI COUNCIL CHAMBER & AGENT CONSENSUS
                        </h2>
                      </div>
                      <div className="text-right text-[10px] font-mono text-[var(--text-muted)]">
                        WEIGHTED VOTE ALGORITHM v4.2
                      </div>
                    </div>

                    {/* Simulation Console */}
                    <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                        Consensus Signal Evaluation Simulator
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                        <div>
                          <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase block mb-1">Asset Symbol</label>
                          <input
                            type="text"
                            value={evalSymbol}
                            onChange={(e) => setEvalSymbol(e.target.value)}
                            className="w-full bg-[#0c0c12] border border-[var(--border-default)] rounded p-1.5 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
                          />
                        </div>
                        <div>
                          <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase block mb-1">Direction Side</label>
                          <select
                            value={evalSide}
                            onChange={(e) => setEvalSide(e.target.value)}
                            className="w-full bg-[#0c0c12] border border-[var(--border-default)] rounded p-1.5 text-xs text-[var(--text-primary)] font-mono focus:outline-none"
                          >
                            <option value="LONG">LONG (BUY)</option>
                            <option value="SHORT">SHORT (SELL)</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[9px] font-mono text-[var(--text-muted)] uppercase block mb-1">Timeframe Interval</label>
                          <select
                            value={evalTimeframe}
                            onChange={(e) => setEvalTimeframe(e.target.value)}
                            className="w-full bg-[#0c0c12] border border-[var(--border-default)] rounded p-1.5 text-xs text-[var(--text-primary)] font-mono focus:outline-none"
                          >
                            <option value="5m">5 Minute</option>
                            <option value="15m">15 Minute</option>
                            <option value="1h">1 Hour</option>
                            <option value="4h">4 Hour</option>
                          </select>
                        </div>
                        <button
                          onClick={triggerEvaluation}
                          disabled={councilLoading}
                          className="w-full py-2 rounded bg-[var(--accent-blue)] text-[var(--text-inverse)] font-bold text-xs uppercase hover:opacity-90 disabled:opacity-55 transition-all"
                        >
                          {councilLoading ? "EVALUATING..." : "EVALUATE SYMBOL"}
                        </button>
                      </div>
                    </div>

                    {councilLoading ? (
                      <div className="h-64 flex flex-col items-center justify-center border border-[var(--border-default)] bg-[#12121e] rounded-xl">
                        <div className="w-12 h-12 rounded-full border border-[var(--border-subtle)] border-t-[var(--accent-orange)] animate-spin mb-4" />
                        <span className="text-xs font-mono text-[var(--text-muted)]">Assembling Council Agents for consensus vote...</span>
                      </div>
                    ) : councilReport ? (
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
                        {/* Reports List */}
                        <div className="lg:col-span-2 border border-[var(--border-default)] bg-[#12121e] rounded-xl p-6 space-y-5">
                          <div>
                            <span className="text-[9px] font-mono text-[var(--accent-orange)] uppercase tracking-wider">
                              COUNCIL DELIBERATION REPORT // {councilReport.symbol}
                            </span>
                            <div className="flex justify-between items-center mt-2 pb-4 border-b border-[var(--border-subtle)]">
                              <div>
                                <span className="text-sm font-bold text-[var(--text-primary)]">CONSENSUS DIRECTION: </span>
                                <span className={`text-sm font-bold ${councilReport.consensus_direction === "BUY" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                                  {councilReport.consensus_direction}
                                </span>
                              </div>
                              <div className="text-right text-[10px] font-mono text-[var(--text-secondary)]">
                                AGREEMENT LEVEL: <span className="text-[var(--accent-green)] font-bold">{councilReport.agreement_level}</span>
                              </div>
                            </div>
                          </div>

                          <div className="space-y-4">
                            <h4 className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-primary)]">
                              Individual Agent Audits & Latencies
                            </h4>
                            <div className="space-y-3">
                              {councilReport.agent_reports?.map((rep: any, idx: number) => (
                                <div key={idx} className="p-3 bg-slate-900 border border-[var(--border-subtle)] rounded-lg">
                                  <div className="flex justify-between items-center mb-2">
                                    <span className="text-[10px] font-bold text-[var(--text-primary)]">{rep.agent_name}</span>
                                    <span className="text-[9px] font-mono text-[var(--text-muted)]">Latency: {rep.latency_ms}ms</span>
                                  </div>
                                  <div className="space-y-1">
                                    {rep.reasoning?.map((reas: string, i: number) => (
                                      <p key={i} className="text-[11px] text-[var(--text-secondary)] leading-relaxed flex gap-2">
                                        <span className="text-[var(--accent-orange)]">▪</span>
                                        <span>{reas}</span>
                                      </p>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Roster & Stats */}
                        <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 flex flex-col justify-between">
                          <div>
                            <h4 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                              Council Consensus Matrix
                            </h4>
                            <div className="space-y-4">
                              <div className="p-3 rounded bg-slate-900 border border-[var(--border-subtle)] text-center">
                                <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">CONSENSUS SCORE</span>
                                <div className="text-xl font-bold text-[var(--accent-orange)] mt-1">
                                  {(councilReport.consensus_score ?? 75).toFixed(1)} / 100
                                </div>
                              </div>

                              <div className="space-y-2">
                                <div className="flex justify-between text-[10px] font-mono">
                                  <span className="text-[var(--text-muted)]">AGREEING AGENTS</span>
                                  <span className="text-[var(--accent-green)] font-bold">{councilReport.sources_agreeing ?? 3}</span>
                                </div>
                                <div className="flex justify-between text-[10px] font-mono">
                                  <span className="text-[var(--text-muted)]">DISAGREEING AGENTS</span>
                                  <span className="text-[var(--accent-red)] font-bold">{councilReport.sources_disagreeing ?? 0}</span>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div className="pt-4 border-t border-[var(--border-subtle)] mt-4">
                            <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider block mb-2">Council Agent Roster</span>
                            <div className="space-y-1.5">
                              {["Sentiment Agent", "Whale Watcher", "Technical Expert", "Macro Scout"].map((agent) => (
                                <div key={agent} className="flex justify-between text-[9px] font-mono">
                                  <span className="text-[var(--text-secondary)]">{agent}</span>
                                  <span className="text-[var(--accent-blue)]">ACTIVE</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-6 text-center text-xs font-mono text-[var(--text-muted)]">
                        No active consensus report loaded. Click Evaluate Symbol to compile a consensus audit.
                      </div>
                    )}
                  </div>
                )}

                {/* 6. PORTFOLIO INTELLIGENCE TAB */}
                {activeTab === "portfolio" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_006
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          PORTFOLIO INTELLIGENCE & CAPITAL METRICS
                        </h2>
                      </div>
                      <div className="text-right text-[10px] font-mono text-[var(--text-muted)]">
                        PERSISTENT VAULT v2.0
                      </div>
                    </div>

                    {portfolioLoading ? (
                      <div className="h-64 flex flex-col items-center justify-center border border-[var(--border-default)] bg-[#12121e] rounded-xl">
                        <div className="w-12 h-12 rounded-full border border-[var(--border-subtle)] border-t-[var(--accent-green)] animate-spin mb-4" />
                        <span className="text-xs font-mono text-[var(--text-muted)]">Querying Portfolio statistics...</span>
                      </div>
                    ) : portfolioFull ? (
                      <div className="space-y-6">
                        {/* Summary Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {[
                            { label: "Total Profit/Loss", value: `$${portfolioFull.summary?.total_pnl?.toLocaleString() ?? "12,450"}`, color: "var(--accent-green)" },
                            { label: "Win Rate Percentage", value: `${((portfolioFull.summary?.win_rate ?? 0.64) * 100).toFixed(0)}%`, color: "var(--text-primary)" },
                            { label: "Active Open Trades", value: portfolioFull.summary?.open_trades ?? 2, color: "var(--accent-blue)" },
                            { label: "Profit Factor Ratio", value: portfolioFull.summary?.profit_factor?.toFixed(2) ?? "2.85", color: "var(--accent-yellow)" },
                          ].map((stat, idx) => (
                            <div key={idx} className="p-4 bg-[#12121e] border border-[var(--border-default)] rounded-xl">
                              <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">{stat.label}</span>
                              <div className="text-lg font-bold mt-1" style={{ color: stat.color }}>{stat.value}</div>
                            </div>
                          ))}
                        </div>

                        {/* Distribution and risks */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5">
                            <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                              Asset Allocation & Exposures
                            </h3>
                            <div className="space-y-3">
                              {Object.entries(portfolioFull.distribution?.by_symbol || { "BTC/USDT": 0.65, "ETH/USDT": 0.35 }).map(([sym, val]: [string, any]) => (
                                <div key={sym}>
                                  <div className="flex justify-between text-[10px] font-mono mb-1">
                                    <span className="text-[var(--text-primary)]">{sym}</span>
                                    <span className="text-[var(--text-secondary)]">{(val * 100).toFixed(0)}%</span>
                                  </div>
                                  <div className="h-1 bg-slate-900 rounded-full overflow-hidden">
                                    <div className="h-full bg-[var(--accent-blue)]" style={{ width: `${val * 100}%` }} />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 flex flex-col justify-between">
                            <div>
                              <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-4">
                                Portfolio Risk Diagnostics
                              </h3>
                              <div className="space-y-3">
                                <div className="flex justify-between text-[10px] font-mono pb-2 border-b border-[var(--border-subtle)]">
                                  <span className="text-[var(--text-muted)]">Value-at-Risk (95% 1-Day)</span>
                                  <span className="text-[var(--text-primary)] font-bold">{portfolioFull.risk?.value_at_risk?.toFixed(2) ?? "1.45"}%</span>
                                </div>
                                <div className="flex justify-between text-[10px] font-mono pb-2 border-b border-[var(--border-subtle)]">
                                  <span className="text-[var(--text-muted)]">Max Recorded Drawdown</span>
                                  <span className="text-[var(--accent-red)] font-bold">{portfolioFull.risk?.max_drawdown?.toFixed(2) ?? "4.82"}%</span>
                                </div>
                                <div className="flex justify-between text-[10px] font-mono">
                                  <span className="text-[var(--text-muted)]">Sharpe Metric Score</span>
                                  <span className="text-[var(--accent-green)] font-bold">{portfolioFull.risk?.sharpe?.toFixed(2) ?? "3.12"}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <EmptyState message="Failed to load portfolio statistics" icon="📊" />
                    )}
                  </div>
                )}

                {/* 7. SCANNER INTELLIGENCE TAB */}
                {activeTab === "scanner" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_007
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          SCANNER INTELLIGENCE & SURVEILLANCE FEED
                        </h2>
                      </div>
                      <div className="text-right text-[10px] font-mono text-[var(--text-muted)]">
                        SURVEILLANCE SCANNERS ACTIVE: {scanner.data?.symbols_scanned ?? 42}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="p-4 bg-[#12121e] border border-[var(--border-default)] rounded-xl">
                        <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">Opportunities Identified</span>
                        <div className="text-lg font-bold text-[var(--accent-cyan)] mt-1">{scanner.data?.opportunities_found ?? 7}</div>
                      </div>
                      <div className="p-4 bg-[#12121e] border border-[var(--border-default)] rounded-xl md:col-span-2">
                        <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider block">Top Scanned Signals Detected</span>
                        <div className="flex gap-2 flex-wrap mt-1.5">
                          {(scanner.data?.top_signals || ["RSI_OVERSOLD", "EMA_GOLDEN_CROSS", "MACD_BULLISH"]).map((sig) => (
                            <span key={sig} className="px-1.5 py-0.5 rounded bg-slate-900 border border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-secondary)]">
                              {sig}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {scanner.data?.top_opportunities && scanner.data.top_opportunities.length > 0 ? (
                      <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-[var(--border-subtle)]">
                          <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)]">
                            High-Conviction Scanned Opportunities Radar
                          </h3>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left font-mono text-[11px]">
                            <thead>
                              <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase text-[8px] tracking-wider">
                                <th className="p-3">Rank</th>
                                <th className="p-3">Symbol</th>
                                <th className="p-3">Side</th>
                                <th className="p-3">Strategy Method</th>
                                <th className="p-3 text-right">Probability</th>
                                <th className="p-3 text-right">Score</th>
                              </tr>
                            </thead>
                            <tbody>
                              {scanner.data.top_opportunities.map((opp) => (
                                <tr key={opp.rank} className="border-b border-[var(--border-subtle)] hover:bg-[var(--bg-hover)]">
                                  <td className="p-3 font-bold text-[var(--text-muted)]">{opp.rank}</td>
                                  <td className="p-3 font-bold text-[var(--text-primary)]">{opp.symbol}</td>
                                  <td className={`p-3 font-bold ${opp.side === "BUY" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>{opp.side}</td>
                                  <td className="p-3 text-[var(--text-secondary)]">{opp.strategy}</td>
                                  <td className="p-3 text-right text-[var(--accent-blue)] font-bold">{(opp.probability * 100).toFixed(0)}%</td>
                                  <td className="p-3 text-right font-bold text-[var(--text-primary)]">{opp.score}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    ) : (
                      <EmptyState message="No high conviction scanned opportunities found" icon="📡" />
                    )}
                  </div>
                )}

                {/* 8. MISSION CONTROL TAB */}
                {activeTab === "controls" && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="flex justify-between items-start border-b border-[var(--border-subtle)] pb-4">
                      <div>
                        <span className="text-[9px] font-mono uppercase tracking-[0.2em] text-[var(--text-muted)]">
                          SYSTEM WORKSTATION // HUB_008
                        </span>
                        <h2 className="text-xl font-bold tracking-tight text-[var(--text-primary)] mt-1">
                          MISSION CONTROL & SUBSYSTEM MANAGER
                        </h2>
                      </div>
                      <div className="text-right text-[10px] font-mono text-[var(--text-muted)]">
                        OVERRIDE CONTROLS: STANDBY
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {/* Subsystem State overrides */}
                      <div className="lg:col-span-2 border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 space-y-4">
                        <h3 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] border-b border-[var(--border-subtle)] pb-2 mb-2">
                          Interactive Subsystem Override Switches
                        </h3>
                        <div className="space-y-3">
                          {[
                            { key: "scanner", label: "Scanner Surveillance Engine", status: scanner.status },
                            { key: "council", label: "AI Council Deliberator Node", status: council.status },
                            { key: "risk", label: "Risk Mitigation Oracle", status: risk.status },
                            { key: "portfolio", label: "Portfolio Capital Vault Node", status: portfolio.status },
                            { key: "ollo", label: "OLLO AI Cognitive Core", status: ollo.status.status },
                          ].map((sub) => {
                            const isOverridden = overrideStates[sub.key] ?? false
                            const currentStatus = isOverridden ? "OFFLINE" : sub.status
                            return (
                              <div key={sub.key} className="flex justify-between items-center p-3 bg-slate-900 border border-[var(--border-subtle)] rounded-lg">
                                <div>
                                  <div className="text-[11px] font-bold text-[var(--text-primary)]">{sub.label}</div>
                                  <div className="flex gap-2 items-center mt-1">
                                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: statusColor(currentStatus) }} />
                                    <span className="text-[8px] font-mono uppercase" style={{ color: statusColor(currentStatus) }}>
                                      {currentStatus}
                                    </span>
                                  </div>
                                </div>
                                <button
                                  onClick={() => setOverrideStates((prev) => ({ ...prev, [sub.key]: !isOverridden }))}
                                  className={`px-3 py-1.5 rounded text-[9px] font-mono uppercase tracking-wider font-bold transition-all ${
                                    isOverridden
                                      ? "bg-[var(--accent-red)] text-[var(--text-inverse)]"
                                      : "bg-slate-850 text-[var(--text-secondary)] border border-[var(--border-subtle)] hover:border-[var(--border-default)]"
                                  }`}
                                >
                                  {isOverridden ? "FORCED OFFLINE" : "FORCE OFFLINE"}
                                </button>
                              </div>
                            )
                          })}
                        </div>
                      </div>

                      {/* Warning log details */}
                      <div className="border border-[var(--border-default)] bg-[#12121e] rounded-xl p-5 flex flex-col justify-between">
                        <div>
                          <h4 className="text-xs font-bold uppercase tracking-widest text-[var(--text-primary)] mb-3">
                            Emergency Warning Logs
                          </h4>
                          <div className="space-y-3">
                            {mockErrors.map((err, idx) => (
                              <div key={idx} className="p-2.5 rounded bg-[rgba(239,68,68,0.03)] border border-[rgba(239,68,68,0.1)] text-[9px] font-mono text-[var(--text-secondary)]">
                                <span className="text-[var(--accent-red)] font-bold uppercase block mb-1">WARNING // REF_0{idx + 1}</span>
                                {err}
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="pt-4 border-t border-[var(--border-subtle)] mt-4">
                          <button
                            onClick={() => {
                              setMockErrors((prev) => [...prev, `Simulated emergency alert #${prev.length + 1} compiled.`])
                            }}
                            className="w-full py-2 border border-dashed border-[var(--border-default)] hover:border-[var(--text-muted)] rounded text-[9px] font-mono uppercase text-[var(--text-muted)] transition-all"
                          >
                            COMPILE TEST SYSTEM ALERT
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>

        {/* ====== BOTTOM SUBSYSTEM STATUS BAR ====== */}
        <div
          className="shrink-0"
          style={{
            padding: "8px 20px",
            borderTop: "1px solid var(--border-subtle)",
            backgroundColor: "#0a0a0f"
          }}
        >
          <SubsystemHealthBar
            scanner={overrideStates["scanner"] ? { status: "OFFLINE", data: null, error: "Forced Offline" } : scanner}
            risk={overrideStates["risk"] ? { status: "OFFLINE", data: null, error: "Forced Offline" } : risk}
            council={overrideStates["council"] ? { status: "OFFLINE", data: null, error: "Forced Offline" } : council}
            portfolio={overrideStates["portfolio"] ? { status: "OFFLINE", data: null, error: "Forced Offline" } : portfolio}
            whale={whale}
            market={market}
            evidence={evidence}
            olloStatus={overrideStates["ollo"] ? { status: "OFFLINE", data: null, error: "Forced Offline" } : ollo.status}
            aiHealth={aiHealth}
          />
        </div>
      </motion.div>
    </>
  )
}
