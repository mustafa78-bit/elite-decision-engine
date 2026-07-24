import { motion } from "framer-motion"
import type { MissionStatus } from "../../types/mission"

interface Props {
  status: MissionStatus
  decisionQuality: string
  evidenceStrength: number
  warnings: number
  currentMission?: string
  aiConnected?: boolean
  aiLatency?: number
  unreadAlerts?: number
  systemStatus?: string
}

function getStatusFromQuality(quality: string, warnings: number): MissionStatus {
  if (quality === "HIGH" && warnings === 0) return "ACTIVE"
  if (quality === "HIGH" && warnings > 0) return "MONITORING"
  if (quality === "MEDIUM") return "MONITORING"
  if (quality === "LOW") return "CAUTION"
  return "CRITICAL"
}

const statusConfig: Record<MissionStatus, { color: string; bg: string; glow: string; label: string }> = {
  ACTIVE: {
    color: "var(--accent-green)",
    bg: "rgba(34, 197, 94, 0.06)",
    glow: "rgba(34, 197, 94, 0.15)",
    label: "All systems nominal. Mission proceeding.",
  },
  MONITORING: {
    color: "var(--accent-blue)",
    bg: "rgba(59, 130, 246, 0.06)",
    glow: "rgba(59, 130, 246, 0.15)",
    label: "Monitoring conditions. No immediate action required.",
  },
  CAUTION: {
    color: "#F97316",
    bg: "rgba(249, 115, 22, 0.06)",
    glow: "rgba(249, 115, 22, 0.15)",
    label: "Caution warranted. Review evidence before proceeding.",
  },
  CRITICAL: {
    color: "var(--accent-red)",
    bg: "rgba(239, 68, 68, 0.06)",
    glow: "rgba(239, 68, 68, 0.15)",
    label: "Critical conditions. Immediate attention required.",
  },
}

export default function MissionStatusBar({
  status: forcedStatus,
  decisionQuality,
  evidenceStrength,
  warnings,
  currentMission,
  aiConnected,
  aiLatency,
  unreadAlerts,
  systemStatus,
}: Props) {
  const status = forcedStatus || getStatusFromQuality(decisionQuality, warnings)
  const config = statusConfig[status]
  const aiOk = aiConnected !== false

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="h-9 flex items-center justify-between px-4 text-[12px] font-mono border-b shrink-0"
      style={{
        backgroundColor: config.bg,
        borderColor: `${config.color}20`,
      }}
    >
      {/* Left: Status + Mission */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{
              backgroundColor: config.color,
              boxShadow: `0 0 8px ${config.glow}`,
              animation: status === "ACTIVE" ? "none" : "ollo-ping 2.5s ease-in-out infinite",
            }}
          />
          <span style={{ color: config.color, fontWeight: 600, letterSpacing: "0.1em" }}>
            {status}
          </span>
          <span className="text-[var(--text-muted)]">·</span>
          <span className="text-[var(--text-muted)] hidden md:inline">{config.label}</span>
        </div>
        {currentMission && (
          <>
            <span className="text-[var(--text-muted)] hidden sm:inline">·</span>
            <span className="text-[var(--text-secondary)] hidden sm:inline">
              Mission: <span style={{ color: config.color }}>{currentMission}</span>
            </span>
          </>
        )}
      </div>

      {/* Right: System info */}
      <div className="flex items-center gap-3">
        {/* AI Health */}
        <div className="flex items-center gap-1.5">
          <span
            className="w-1 h-1 rounded-full"
            style={{ backgroundColor: aiOk ? "#22C55E" : "#EF4444" }}
          />
          <span className="text-[var(--text-muted)]">
            AI {aiOk ? "OK" : "ERR"}
            {aiLatency !== undefined && aiOk && (
              <span className="ml-1">{aiLatency.toFixed(0)}ms</span>
            )}
          </span>
        </div>

        {/* Alerts */}
        {unreadAlerts !== undefined && (
          <span
            className="text-[var(--text-muted)]"
            style={unreadAlerts > 0 ? { color: "#F97316" } : undefined}
          >
            {unreadAlerts > 0 ? `${unreadAlerts} mission alert${unreadAlerts > 1 ? 's' : ''}` : "0 mission alerts"}
          </span>
        )}

        {/* Evidence */}
        <span className="text-[var(--text-muted)] hidden sm:inline">
          Evidence: <span style={{ color: "var(--accent-blue)" }}>{(evidenceStrength * 100).toFixed(0)}%</span>
        </span>

        {/* Quality */}
        <span className="text-[var(--text-muted)] hidden md:inline">
          Quality: <span style={{
            color: decisionQuality === "HIGH" ? "#22C55E" :
                   decisionQuality === "LOW" ? "#F97316" :
                   decisionQuality === "MEDIUM" ? "#FACC15" : "#64748B"
          }}>
            {decisionQuality}
          </span>
        </span>

        {/* System status */}
        {systemStatus && (
          <span className="text-[var(--text-muted)] hidden lg:inline">
            {systemStatus}
          </span>
        )}
      </div>
    </motion.div>
  )
}
