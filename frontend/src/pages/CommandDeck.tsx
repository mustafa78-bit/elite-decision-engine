import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { useSubsystems } from "../hooks/useSubsystems"
import { computeMissionStatus } from "../types/mission"
import OLLOCommander from "../components/hq/OLLOCommander"
import MissionRing from "../components/hq/MissionRing"
import MissionFlow from "../components/hq/MissionFlow"
import SubsystemHealthBar from "../components/hq/SubsystemHealthBar"
import HQLoadingScreen from "../components/hq/HQLoadingScreen"
import type { SubsystemStatus } from "../types/system"

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
        style={{ fontSize: 11, color: "var(--text-muted)", width: 90, letterSpacing: "0.05em" }}
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
        style={{ fontSize: 11, color, width: 28, textAlign: "right" as const }}
      >
        {pct.toFixed(0)}%
      </span>
    </div>
  )
}

export default function CommandDeck() {
  const [showLoading, setShowLoading] = useState(true)

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
        className="h-full flex flex-col"
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
              className="text-[11px] font-semibold uppercase tracking-[0.22em]"
              style={{ color: "var(--text-primary)" }}
            >
              COMMAND HEADQUARTERS
            </span>
            <span
              className="text-[11px] font-mono uppercase tracking-[0.15em]"
              style={{ color: "var(--text-muted)" }}
            >
              · Founder Alpha
            </span>
            {currentMission && (
              <>
                <span className="text-[11px]" style={{ color: "var(--border-subtle)" }}>·</span>
                <span
                  className="text-[11px] font-mono uppercase tracking-[0.1em]"
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
                className="text-[11px] font-semibold uppercase tracking-[0.12em]"
                style={{ color: missionColor }}
              >
                {missionStatus}
              </span>
            </div>

            <span className="text-[11px]" style={{ color: "var(--border-subtle)" }}>|</span>

            <span
              className="text-[11px] font-mono tabular-nums"
              style={{ color: "var(--text-muted)" }}
            >
              {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
            </span>

            <div className="flex items-center gap-1">
              <span
                className="w-1 h-1 rounded-full"
                style={{ backgroundColor: aiConnected !== false ? "#3EDC97" : "#FF5D73" }}
              />
              <span className="text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
                AI {aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : "OK") : "ERR"}
              </span>
            </div>

            {warnings.length > 0 && (
              <span className="text-[11px] font-mono" style={{ color: "var(--accent-yellow)" }}>
                {warnings.length} alert{warnings.length > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </header>

        {/* ====== CONTENT — unified vertical flow ====== */}
        <div className="flex-1 overflow-y-auto">
          {/* 1 + 2: OLLO + Mission Ring */}
          <div className="hq-section flex flex-col items-center py-10">
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
          </div>

          {/* 3: Current Recommendation */}
          {recommendation && (
            <div className="hq-section">
              <div className="max-w-xl mx-auto">
                <div className="hq-section-label">Current Recommendation</div>
                <p
                  className="text-sm font-semibold leading-snug"
                  style={{ color: "var(--text-primary)" }}
                >
                  {recommendation}
                </p>
              </div>
            </div>
          )}

          {/* 4: Evidence */}
          {(confidence !== null || strength !== null || explainability !== null) && (
            <div className="hq-section">
              <div className="max-w-xl mx-auto">
                <div className="hq-section-label">Evidence</div>
                <div className="space-y-2">
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
                </div>

                {/* Counts */}
                {(supportingCount !== null || conflictCount !== null || warningCount !== null) && (
                  <div className="flex items-center gap-4 mt-3">
                    {supportingCount !== null && (
                      <span className="text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
                        <span style={{ color: "var(--accent-green)" }}>{supportingCount}</span> supporting
                      </span>
                    )}
                    {conflictCount !== null && conflictCount > 0 && (
                      <span className="text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
                        <span style={{ color: "var(--accent-red)" }}>{conflictCount}</span> conflicting
                      </span>
                    )}
                    {warningCount !== null && warningCount > 0 && (
                      <span className="text-[11px] font-mono" style={{ color: "var(--text-muted)" }}>
                        <span style={{ color: "var(--accent-yellow)" }}>{warningCount}</span> warnings
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 5: Mission Flow */}
          <div className="hq-section">
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
