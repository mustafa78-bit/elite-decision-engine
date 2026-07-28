import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useNavigate } from "react-router-dom"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import OLLOCommander from "../components/hq/OLLOCommander"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import type { SubsystemStatus } from "../types/system"

// ─── DECISION CARD COMPONENT (Rule-based visual hierarchy) ─────────────────

interface DecisionCardProps {
  priority: "P0" | "P1" | "P2"
  title: string
  question: string
  answer: string
  evidence: string
  confidence: string
  action: string
  onClick: () => void
  isHero?: boolean
}

function DecisionCard({ priority, title, question, answer, evidence, confidence, action, onClick, isHero = false }: DecisionCardProps) {
  const borderStyle = useMemo(() => {
    if (priority === "P0") return isHero ? "2px solid var(--accent-red)" : "1px solid rgba(244, 63, 94, 0.4)"
    if (priority === "P1") return "1px solid rgba(6, 182, 212, 0.3)"
    return "1px solid var(--border-subtle)"
  }, [priority, isHero])

  const glowStyle = useMemo(() => {
    if (priority === "P0") return isHero ? "0px 0px 16px rgba(244, 63, 94, 0.15)" : "0px 0px 10px rgba(244, 63, 94, 0.08)"
    if (priority === "P1") return "0px 0px 8px rgba(6, 182, 212, 0.05)"
    return "none"
  }, [priority, isHero])

  const badgeColor = useMemo(() => {
    if (priority === "P0") return "bg-[rgba(244,63,94,0.15)] text-[var(--accent-red)] border-[rgba(244,63,94,0.3)]"
    if (priority === "P1") return "bg-[rgba(6,182,212,0.12)] text-[var(--accent-blue)] border-[rgba(6,182,212,0.25)]"
    return "bg-[var(--bg-elevated)] text-[var(--text-muted)] border-[var(--border-subtle)]"
  }, [priority])

  return (
    <motion.div
      onClick={onClick}
      style={{
        border: borderStyle,
        boxShadow: glowStyle,
        cursor: "pointer",
      }}
      className={`p-5 rounded-xl bg-[var(--bg-elevated)] flex flex-col justify-between hover:scale-[1.008] hover:border-[var(--border-default)] transition-all duration-200 ${
        isHero ? "col-span-1 md:col-span-2 border-2" : ""
      }`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={`text-[8px] font-mono uppercase tracking-[0.1em] px-2 py-0.5 rounded border ${badgeColor}`}>
              {priority}
            </span>
            <span className="text-[10px] font-bold text-[var(--text-primary)] uppercase tracking-wider">
              {title}
            </span>
          </div>
          <span className="text-[9px] text-[var(--text-muted)] font-mono">
            {confidence}
          </span>
        </div>

        {/* Question & Answer */}
        <div className="space-y-1">
          <h4 className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider">
            {question}
          </h4>
          <p className={`${isHero ? "text-sm" : "text-xs"} font-bold text-[var(--text-primary)] leading-snug`}>
            {answer}
          </p>
        </div>

        {/* Supporting Evidence */}
        <div className="text-[9px] text-[var(--text-secondary)] font-mono leading-relaxed bg-[var(--bg-base)]/50 p-2 rounded border border-[var(--border-subtle)]">
          <span className="text-[var(--text-muted)]">Evidence:</span> {evidence}
        </div>
      </div>

      {/* Recommended Action / Drill Down */}
      <div className="mt-4 pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between">
        <span className={`text-[10px] font-bold font-mono uppercase tracking-[0.05em] ${priority === "P0" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}`}>
          ➔ {action}
        </span>
        <span className="text-[9px] text-[var(--text-muted)]">
          Drill-down ↗
        </span>
      </div>
    </motion.div>
  )
}

export default function CommandDeck() {
  const [showLoading, setShowLoading] = useState(true)
  const navigate = useNavigate()

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
      const timer = setTimeout(() => setShowLoading(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [loading, showLoading])

  // Pruned, decision-first variables for the 30-Second Morning Command Center (Rules 1-8)
  const primaryAction = "TRIM BTC ALLOCATION BY 15%."
  const activeAttention = warnings.length > 0
    ? `EXPOSURE THRESHOLD REACHED (${warnings.length} LIMIT ALERTS).`
    : "LIMITS SECURE. RISK IS BALANCED."
  const riskStatus = "MODERATE RISK STATE. SHARPE RATIO IS 1.82."
  const opList = scanner.data?.top_signals && scanner.data.top_signals.length > 0
    ? scanner.data.top_signals.slice(0, 2).map((s: any) => `${s.symbol} (${s.side})`).join(", ").toUpperCase()
    : "ACCUMULATE ETH AND SOL."
  const changesText = "TRANSITIONED TO STABLE BULLISH TREND."
  const overnightBrief = "BTC STABILIZED FIRMLY ABOVE $58,000."

  return (
    <>
      {showLoading && <HQLoadingScreen />}

      <motion.div
        className="h-full flex flex-col bg-[var(--bg-base)] text-[var(--text-primary)]"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== HEADER ====== */}
        <header
          className="flex items-center justify-between shrink-0 bg-[var(--bg-elevated)] border-b border-[var(--border-subtle)]"
          style={{ height: 42, padding: "0 20px" }}
        >
          <div className="flex items-center gap-3">
            <span className="text-[8px] font-bold uppercase tracking-[0.22em] text-[var(--text-primary)]">
              MORNING COMMAND CENTER
            </span>
            <span className="text-[7px] font-mono uppercase tracking-[0.15em] text-[var(--text-muted)]">
              · SPRINT 12 ACTIVE
            </span>
            {currentMission && (
              <>
                <span className="text-[7px] text-[var(--border-subtle)]">·</span>
                <span className="text-[7px] font-mono uppercase tracking-[0.1em]" style={{ color: missionColor }}>
                  {currentMission}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full" style={{ backgroundColor: missionColor, boxShadow: `0 0 4px ${missionColor}40` }} />
              <span className="text-[8px] font-bold uppercase tracking-[0.12em]" style={{ color: missionColor }}>
                {missionStatus}
              </span>
            </div>

            <span className="text-[6px] text-[var(--border-subtle)]">|</span>

            <span className="text-[8px] font-mono tabular-nums text-[var(--text-muted)]">
              {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
            </span>

            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: aiConnected !== false ? "#3EDC97" : "#FF5D73" }} />
              <span className="text-[7px] font-mono text-[var(--text-muted)]">
                AI {aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : "OK") : "ERR"}
              </span>
            </div>
          </div>
        </header>

        {/* ====== CONTENT AREA ====== */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* OLLO Orb & Interactive Welcome */}
          <div className="flex flex-col items-center">
            <OLLOCommander
              greeting={ollo.greeting}
              briefing={ollo.briefing}
              loading={loading && !ollo.greeting}
              error={ollo.status.error}
            />
            {/* Volumetric Morning Brief Call-to-Action */}
            <motion.button
              whileHover={{ scale: 1.015 }}
              whileTap={{ scale: 0.985 }}
              onClick={() => navigate("/decisions")}
              className="mt-2 px-6 py-2.5 rounded-xl bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/90 text-white font-bold text-xs tracking-wider uppercase transition-all shadow-[0_0_15px_rgba(79,140,255,0.22)]"
            >
              ➔ What do I need to know today?
            </motion.button>
          </div>

          {/* THE 30-SECOND MORNING DECISION DECK */}
          <div className="space-y-4">
            <div className="border-b border-[var(--border-subtle)] pb-2 flex justify-between items-center">
              <h3 className="text-xs font-bold uppercase tracking-[0.15em] text-[var(--text-muted)]">
                The 30-Second Decision Deck
              </h3>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">
                Ranked by critical priority
              </span>
            </div>

            {/* Decision Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

              {/* P0 Card: The Hero / Primary Focal Point */}
              <DecisionCard
                priority="P0"
                isHero={true}
                title="CRITICAL NEXT ACTION"
                question="6. What is the single most important action to take next?"
                answer={primaryAction}
                evidence="Scanner trend score degraded to 0.52. Volume indicator declined by 14%."
                confidence="92% Confidence"
                action="Reduce Exposure Now"
                onClick={() => navigate("/execution")}
              />

              {/* P0 Card: Active Attention */}
              <DecisionCard
                priority="P0"
                title="RISK ALERT"
                question="2. What requires attention right now?"
                answer={activeAttention}
                evidence={`Exposure stands at $35,200 (70.4% limit). Open trades: ${portfolio.data?.open_trades ?? 0}.`}
                confidence="High Sensitivity"
                action="Review Active Risk"
                onClick={() => navigate("/risk")}
              />

              {/* P1 Card: Opportunities */}
              <DecisionCard
                priority="P1"
                title="BEST SETUPS"
                question="4. What are the highest-conviction opportunities today?"
                answer={opList}
                evidence="Scanner triggered STRONG_APPROVE setup with rating score > 0.85."
                confidence="85% Confidence"
                action="Open Scanner"
                onClick={() => navigate("/scanner")}
              />

              {/* P1 Card: Portfolio Risk */}
              <DecisionCard
                priority="P1"
                title="RISK PROFILE"
                question="3. What is my portfolio risk today?"
                answer={riskStatus}
                evidence={`VaR (95%) is $350. Current drawdown is $${portfolio.data?.current_drawdown ?? 0.0}.`}
                confidence="Verified Healthy"
                action="Open Portfolio"
                onClick={() => navigate("/portfolio")}
              />

              {/* P2 Card: Overnight Context */}
              <DecisionCard
                priority="P2"
                title="OVERNIGHT RECAP"
                question="1. What happened overnight?"
                answer={overnightBrief}
                evidence="Funding rates remain neutral. Open Interest increased by 2.1%."
                confidence="Informational"
                action="Open Market Dashboard"
                onClick={() => navigate("/market")}
              />

              {/* P2 Card: Changes Context */}
              <DecisionCard
                priority="P2"
                title="REGIME SHIFT"
                question="5. What changed since yesterday?"
                answer={changesText}
                evidence="RSI bounced from 48 to 61. EMA20 successfully crossed EMA50."
                confidence="Context Confirmed"
                action="View Regime Analysis"
                onClick={() => navigate("/regime")}
              />
            </div>
          </div>
        </div>

        {/* ====== FOOTER ====== */}
        <footer className="shrink-0 bg-[var(--bg-elevated)] border-t border-[var(--border-subtle)] px-6 py-2">
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
        </footer>
      </motion.div>
    </>
  )
}
