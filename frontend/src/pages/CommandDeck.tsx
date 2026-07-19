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
    case "ONLINE": return "#10B981" // Premium Mint Green
    case "DEGRADED": return "#F59E0B" // Premium Amber
    case "OFFLINE": return "#EF4444" // Soft Rose Red
    case "UNKNOWN": return "#64748B" // Slate Gray
  }
}

function qualityColor(q: string): string {
  switch (q) {
    case "HIGH": return "#10B981"
    case "MEDIUM": return "#F59E0B"
    case "LOW": return "#EF4444"
    default: return "#64748B"
  }
}

function ProgressLine({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="flex items-center gap-4 bg-slate-50/50 p-3 rounded-xl border border-slate-100">
      <span
        className="font-mono font-bold shrink-0 text-left text-[10px]"
        style={{ color: "var(--text-secondary)", width: 140, letterSpacing: "0.08em" }}
      >
        {label}
      </span>
      <div
        className="flex-1 h-2 rounded-full overflow-hidden bg-slate-200/50"
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
        className="font-mono tabular-nums shrink-0 font-bold text-xs"
        style={{ color, width: 36, textAlign: "right" as const }}
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
    { label: "Founder" as const, active: true, color: "#2563EB" },
    { label: "Action" as const, active: true, color: "#3B82F6" },
  ], [scanner.status, whale.status, council.status, evidence.status, aiHealth.status])

  const missionColor = useMemo(() => {
    switch (missionStatus) {
      case "ACTIVE": return "#10B981"
      case "MONITORING": return "#2563EB"
      case "CAUTION": return "#F59E0B"
      case "CRITICAL": return "#EF4444"
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
        className="h-full flex flex-col bg-[#f8f9fc]"
        initial={{ opacity: 0 }}
        animate={{ opacity: showLoading ? 0 : 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {/* ====== TOP BAR ====== */}
        <header
          className="flex items-center justify-between shrink-0 bg-white border-b border-slate-200"
          style={{
            height: 48,
            padding: "0 24px",
          }}
        >
          <div className="flex items-center gap-3">
            <span
              className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-900"
            >
              COMMAND HEADQUARTERS
            </span>
            <span
              className="text-[10px] font-mono uppercase tracking-widest text-[var(--text-muted)] font-medium"
            >
              · Founder Alpha
            </span>
            {currentMission && (
              <>
                <span className="text-slate-200">·</span>
                <span
                  className="text-[10px] font-mono uppercase tracking-wider font-bold"
                  style={{ color: missionColor }}
                >
                  {currentMission}
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-100 px-2.5 py-1 rounded-full">
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: missionColor, boxShadow: `0 0 8px ${missionColor}60` }}
              />
              <span
                className="text-[9px] font-bold uppercase tracking-wider font-mono"
                style={{ color: missionColor }}
              >
                {missionStatus}
              </span>
            </div>

            <span className="text-slate-200">|</span>

            <span
              className="text-xs font-mono font-semibold text-[var(--text-secondary)]"
            >
              {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
            </span>

            <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-100 px-2.5 py-1 rounded-full">
              <span
                className="w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: aiConnected !== false ? "#10B981" : "#EF4444" }}
              />
              <span className="text-[9px] font-mono font-bold text-[var(--text-secondary)]">
                AI {aiConnected !== false ? (aiLatency ? `${aiLatency.toFixed(0)}ms` : "ACTIVE") : "OFFLINE"}
              </span>
            </div>

            {warnings.length > 0 && (
              <span className="text-[10px] font-mono font-bold text-amber-600 bg-amber-50 border border-amber-200/50 px-2.5 py-1 rounded-full">
                {warnings.length} alert{warnings.length > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </header>

        {/* ====== CONTENT — unified vertical flow ====== */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* 1 + 2: OLLO + Mission Ring */}
          <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-[0_4px_16px_rgba(15,23,42,0.03)] flex flex-col items-center">
            <div className="relative flex flex-col items-center w-full max-w-2xl">
              <OLLOCommander
                greeting={ollo.greeting}
                briefing={ollo.briefing}
                loading={loading && !ollo.greeting}
                error={ollo.status.error}
              />
              <div className="mt-8 border-t border-slate-100 pt-8 w-full flex justify-center">
                <MissionRing sectors={sectors} />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 3: Current Recommendation */}
            {recommendation && (
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-[0_2px_8px_rgba(15,23,42,0.02)]">
                <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-3">
                  Current Recommendation
                </div>
                <p
                  className="text-sm font-semibold leading-relaxed text-slate-800"
                >
                  {recommendation}
                </p>
              </div>
            )}

            {/* 4: Evidence */}
            {(confidence !== null || strength !== null || explainability !== null) && (
              <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-[0_2px_8px_rgba(15,23,42,0.02)]">
                <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-3">
                  Evidence Telemetry
                </div>
                <div className="space-y-2.5">
                  {confidence !== null && (
                    <ProgressLine
                      value={confidence}
                      label="Decision Confidence"
                      color={qualityColor(decisionQuality ?? "UNKNOWN")}
                    />
                  )}
                  {strength !== null && (
                    <ProgressLine value={strength} label="Evidence Strength" color="#2563EB" />
                  )}
                  {explainability !== null && (
                    <ProgressLine value={explainability} label="Explainability Score" color="#7C3AED" />
                  )}
                </div>

                {/* Counts */}
                {(supportingCount !== null || conflictCount !== null || warningCount !== null) && (
                  <div className="flex items-center gap-4 mt-4 border-t border-slate-100 pt-3">
                    {supportingCount !== null && (
                      <span className="text-[10px] font-mono font-bold text-slate-500 bg-emerald-50 border border-emerald-100/50 px-2 py-0.5 rounded-md">
                        <span className="text-emerald-700">{supportingCount}</span> supporting
                      </span>
                    )}
                    {conflictCount !== null && conflictCount > 0 && (
                      <span className="text-[10px] font-mono font-bold text-slate-500 bg-red-50 border border-red-100/50 px-2 py-0.5 rounded-md">
                        <span className="text-red-700">{conflictCount}</span> conflicting
                      </span>
                    )}
                    {warningCount !== null && warningCount > 0 && (
                      <span className="text-[10px] font-mono font-bold text-slate-500 bg-amber-50 border border-amber-100/50 px-2 py-0.5 rounded-md">
                        <span className="text-amber-700">{warningCount}</span> warnings
                      </span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* 5: Mission Flow */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-[0_2px_8px_rgba(15,23,42,0.02)]">
            <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)] mb-4">
              Real-Time Signal Pipeline
            </div>
            <div className="max-w-4xl mx-auto py-2">
              <MissionFlow nodes={flowNodes} />
            </div>
          </div>
        </div>

        {/* ====== BOTTOM: Subsystem Health ====== */}
        <div
          className="shrink-0 bg-white border-t border-slate-200"
          style={{
            padding: "12px 24px",
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
