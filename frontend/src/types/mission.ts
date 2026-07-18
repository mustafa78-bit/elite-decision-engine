export type MissionStatus = "ACTIVE" | "MONITORING" | "CAUTION" | "CRITICAL"

export interface MissionState {
  status: MissionStatus
  label: string
  description: string
}

export function computeMissionStatus(
  riskScore: number | null,
  decisionQuality: string | null,
  aiConnected: boolean | null,
  offlineSubsystems: number,
): MissionStatus {
  const hasAI = aiConnected !== false
  const hasRisk = riskScore !== null
  const riskOk = riskScore !== null && riskScore < 50
  const qualityOk = decisionQuality === "HIGH"
  const qualityMedium = decisionQuality === "MEDIUM"
  const qualityLow = decisionQuality === "LOW"

  if (offlineSubsystems > 2 || !hasAI) return "CRITICAL"
  if (offlineSubsystems > 0) return "CAUTION"
  if (!hasRisk) return "CAUTION"
  if (riskScore !== null && riskScore > 80) return "CRITICAL"
  if (riskScore !== null && riskScore > 50) return "CAUTION"
  if (qualityLow) return "CAUTION"
  if (qualityMedium) return "MONITORING"
  if (riskScore !== null && riskScore > 30) return "MONITORING"
  if (!qualityOk && riskOk) return "MONITORING"
  return "ACTIVE"
}
