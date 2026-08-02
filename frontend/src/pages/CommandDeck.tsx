import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import { NexusDashboard } from "../components/hq/NexusDashboard"
import MissionFlow from "../components/hq/MissionFlow"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import type { SubsystemStatus } from "../types/system"

// Merged components/imports from AIExperience
import { SignalFeed } from "../components/ai/signal-feed"
import { AnalysisDashboard } from "../components/ai/analysis-dashboard"
import ScannerOpportunitiesPanel from "../components/dashboard/ScannerOpportunitiesPanel"
import { apiFetch } from "../api/client"

interface SignalData {
  id: number;
  symbol: string;
  side: string;
  decision: string;
  confidence: number;
  final_score: number;
  price: number | null;
  created_at: string | null;
}

interface MarketData {
  price: number;
  regime: string;
  volatility: number;
  rsi: number;
}

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
        style={{ fontSize: 8, color: "var(--text-muted)", width: 90, letterSpacing: "0.05em" }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-px rounded-full overflow-hidden"
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

export default function CommandDeck() {
  const [showLoading, setShowLoading] = useState(true)
  const [signals, setSignals] = useState<SignalData[]>([])
  const [marketData, setMarketData] = useState<MarketData | null>(null)

  const {
    scanner, risk, council, portfolio, whale, market, evidence,
    ollo, aiHealth, loading,
  } = useSubsystems()

  // Fetch signals & market data for surrounding dashboard panels
  useEffect(() => {
    let mounted = true
    Promise.all([
      apiFetch<SignalData[]>("/signals?limit=10").catch(() => [] as SignalData[]),
      apiFetch<{ price?: number; regime?: string; volatility?: number; rsi?: number }>("/market").catch((): { price?: number; regime?: string; volatility?: number; rsi?: number } => ({})),
    ]).then(([sigData, mktData]) => {
      if (!mounted) return
      setSignals(Array.isArray(sigData) ? sigData : [])
      if (mktData.price) {
        setMarketData({
          price: mktData.price,
          regime: mktData.regime || "UNKNOWN",
          volatility: mktData.volatility || 0,
          rsi: mktData.rsi || 50,
        })
      }
    })
    return () => { mounted = false }
  }, [])

  const signalItems = useMemo(() => signals.slice(0, 5).map((s) => ({
    id: String(s.id),
    symbol: s.symbol,
    direction: (s.side === "BUY" || s.side === "LONG" ? "BUY" : s.side === "SELL" || s.side === "SHORT" ? "SELL" : "NEUTRAL") as "BUY" | "SELL" | "NEUTRAL",
    strength: s.final_score,
    strategy: s.decision || "AI Signal",
    price: s.price || 0,
    timestamp: s.created_at || new Date().toISOString(),
  })), [signals])

  const analysisItems = useMemo(() => marketData
    ? [
        { label: "Trend", value: marketData.regime, score: marketData.regime === "TREND" ? 82 : marketData.regime === "DOWNTREND" ? 25 : 50, status: (marketData.regime === "TREND" ? "bullish" : marketData.regime === "DOWNTREND" ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Momentum", value: marketData.rsi >= 60 ? "Positive" : marketData.rsi <= 40 ? "Negative" : "Neutral", score: marketData.rsi, status: (marketData.rsi >= 60 ? "bullish" : marketData.rsi <= 40 ? "bearish" : "neutral") as "bullish" | "bearish" | "neutral" },
        { label: "Volatility", value: marketData.volatility >= 0.5 ? "High" : marketData.volatility >= 0.2 ? "Moderate" : "Low", score: Math.round(marketData.volatility * 100), status: "neutral" as const },
        { label: "Price", value: `$${marketData.price.toLocaleString()}`, score: 50, status: "neutral" as const },
      ]
    : [], [marketData])

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

  const recommendation = evidence.data?.recommendation || null
  const confidence = evidence.data?.decision_confidence ?? null
  const strength = evidence.data?.evidence_strength ?? null
  const explainability = evidence.data?.explainability ?? null
  const supportingCount = evidence.data?.supporting_evidence.length ?? null
  const conflictCount = evidence.data?.contradicting_evidence.length ?? null
  const warningCount = evidence.data?.warnings.length ?? null

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
        className="h-full flex flex-col overflow-y-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== NEXUS HERO: just the brain + voice/chat console, no cards ====== */}
        <NexusDashboard
          olloGreeting={ollo.greeting}
          olloBriefing={ollo.briefing}
          olloLoading={loading && !ollo.greeting}
          olloError={ollo.status.error}
          onEnterCommandDeck={() => document.getElementById("command-deck-panels")?.scrollIntoView({ behavior: "smooth" })}
        />

        {/* ====== MISSION STATUS STRIP ====== */}
        <div
          id="command-deck-panels"
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
              COMMAND HEADQUARTERS
            </span>
            <span
              className="text-[7px] font-mono uppercase tracking-[0.15em]"
              style={{ color: "var(--text-muted)" }}
            >
              · Founder Alpha
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
                className="w-1 h-1 rounded-full"
                style={{ backgroundColor: missionColor, boxShadow: `0 0 4px ${missionColor}40` }}
              />
              <span
                className="text-[8px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: missionColor }}
              >
                {missionStatus}
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
        </div>

        {/* ====== CONTENT — Evidence, Mission Flow & Merged AI Experience Side Panels ====== */}
        <div className="flex-1 grid grid-cols-1 xl:grid-cols-4 gap-6 p-6">

          {/* Side Panel Left: Signal Feed + Ranked Opportunities */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <SignalFeed signals={signalItems} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
            >
              <ScannerOpportunitiesPanel />
            </motion.div>
          </div>

          {/* Centre: Recommendation / Evidence / Mission Flow */}
          <div className="xl:col-span-2 flex flex-col items-center gap-6">
            {/* Recommendation (Grounded details) */}
            {recommendation && (
              <div className="w-full max-w-xl">
                <div className="hq-section-label">Current Recommendation</div>
                <div className="p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  <p
                    className="text-xs font-semibold leading-relaxed"
                    style={{ color: "var(--text-primary)" }}
                  >
                    {recommendation}
                  </p>
                </div>
              </div>
            )}

            {/* Evidence details */}
            {(confidence !== null || strength !== null || explainability !== null) && (
              <div className="w-full max-w-xl">
                <div className="hq-section-label">Evidence Analysis</div>
                <div className="space-y-3 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
                  {confidence !== null && (
                    <ProgressLine
                      value={confidence}
                      label="Decision Confidence"
                      color={qualityColor(decisionQuality ?? "UNKNOWN")}
                    />
                  )}
                  {strength !== null && (
                    <ProgressLine value={strength} label="Evidence Strength" color="#4F8CFF" />
                  )}
                  {explainability !== null && (
                    <ProgressLine value={explainability} label="Explainability" color="#8B5CF6" />
                  )}

                  {/* Counts */}
                  {(supportingCount !== null || conflictCount !== null || warningCount !== null) && (
                    <div className="flex items-center gap-4 mt-3 pt-2 border-t border-[var(--border-subtle)]">
                      {supportingCount !== null && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#3EDC97" }}>{supportingCount}</span> supporting
                        </span>
                      )}
                      {conflictCount !== null && conflictCount > 0 && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#FF5D73" }}>{conflictCount}</span> conflicting
                        </span>
                      )}
                      {warningCount !== null && warningCount > 0 && (
                        <span className="text-[7px] font-mono" style={{ color: "var(--text-muted)" }}>
                          <span style={{ color: "#FFB547" }}>{warningCount}</span> warnings
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Mission Flow */}
            <div className="w-full max-w-xl">
              <MissionFlow nodes={flowNodes} />
            </div>
          </div>

          {/* Side Panel Right: Market Analysis */}
          <div className="xl:col-span-1 flex flex-col gap-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.15 }}
            >
              <AnalysisDashboard symbol="BTC/USDT" items={analysisItems} />
            </motion.div>
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
