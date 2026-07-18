export type SubsystemStatus = "ONLINE" | "DEGRADED" | "OFFLINE" | "UNKNOWN"

export interface SubsystemState<T = unknown> {
  status: SubsystemStatus
  data: T | null
  error: string | null
}

export interface SubsystemHealth {
  scanner: SubsystemState
  risk: SubsystemState
  council: SubsystemState
  portfolio: SubsystemState
  whale: SubsystemState
  market: SubsystemState
  evidence: SubsystemState
  ollo: SubsystemState
  aiHealth: SubsystemState
}
