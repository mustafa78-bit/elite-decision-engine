import type { SubsystemState } from "../../types/system"
import type { ScannerDashboard } from "../../api/scanner"
import type { RiskData } from "../../api/risk"
import type { CouncilStatusData } from "../../api/council"
import type { PortfolioSummaryDTO } from "../../types/api/portfolio"
import type { WhaleActivity } from "../../api/whale"
import type { MarketData } from "../../api/market"
import type { EvidenceReport } from "../../types/evidence"
import type { OLLOStatus } from "../../types/ollo"
import type { AIHealthResponse } from "../../api/ai-health"

interface Props {
  scanner: SubsystemState<ScannerDashboard>
  risk: SubsystemState<RiskData>
  council: SubsystemState<CouncilStatusData>
  portfolio: SubsystemState<PortfolioSummaryDTO>
  whale: SubsystemState<WhaleActivity[]>
  market: SubsystemState<MarketData>
  evidence: SubsystemState<EvidenceReport>
  olloStatus: SubsystemState<OLLOStatus>
  aiHealth: SubsystemState<AIHealthResponse>
}

const statusColor: Record<string, string> = {
  ONLINE: "#3EDC97",
  OFFLINE: "#FF5D73",
  DEGRADED: "#FFB547",
  UNKNOWN: "#6B7891",
}

function StatusDot({ status, label }: { status: string; label: string }) {
  const color = statusColor[status] || "#6B7891"
  return (
    <div className="flex items-center gap-1.5">
      <span
        className="rounded-full"
        style={{
          width: 5,
          height: 5,
          backgroundColor: color,
          opacity: status === "UNKNOWN" ? 0.25 : 0.7,
          transition: "all 0.3s ease",
        }}
      />
      <span
        className="font-mono"
        style={{
          fontSize: 8,
          color: "var(--text-muted)",
          letterSpacing: "0.05em",
        }}
      >
        {label}
      </span>
      <span
        className="font-mono"
        style={{
          fontSize: 6,
          color: color,
          opacity: 0.4,
          textTransform: "uppercase" as const,
          letterSpacing: "0.08em",
        }}
      >
        {status === "UNKNOWN" ? "?" : status}
      </span>
    </div>
  )
}

export default function SubsystemHealthBar({
  scanner, risk, council, portfolio, whale, market, evidence, olloStatus, aiHealth,
}: Props) {
  const allSystems = [
    { label: "Scanner", status: scanner.status },
    { label: "Risk", status: risk.status },
    { label: "Council", status: council.status },
    { label: "Portfolio", status: portfolio.status },
    { label: "Whale", status: whale.status },
    { label: "Market", status: market.status },
    { label: "Evidence", status: evidence.status },
    { label: "OLLO", status: olloStatus.status },
    { label: "AI", status: aiHealth.status },
  ]

  const onlineCount = allSystems.filter((s) => s.status === "ONLINE").length
  const totalCount = allSystems.length

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3 flex-wrap">
        {allSystems.map((s) => (
          <StatusDot key={s.label} label={s.label} status={s.status} />
        ))}
      </div>
      <span
        className="font-mono tabular-nums shrink-0"
        style={{ fontSize: 7, color: "var(--text-muted)" }}
      >
        {onlineCount}/{totalCount}
      </span>
    </div>
  )
}
