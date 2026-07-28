import { apiFetch } from "./client"

export interface TrustSummary {
  symbol: string
  trust_score: number
  alignment: number
  accuracy: number
  integrity: number
  reliability: number
  stats: {
    symbol: string
    accuracy: number
    total_completed: number
    correct_count: number
    incorrect_count: number
  }
}

export interface TrustHistoryItem {
  decision_id: string
  symbol: string
  predicted_direction: string
  predicted_confidence: number
  actual_outcome: string
  pnl: number | null
  timestamp: string
  provenance_hash: string
  inputs_fingerprint: string
}

export interface TrustEvidence {
  decision_id: string
  why: string[]
  evidence_count: number
  supporting_count: number
  contradicting_count: number
  events: any[]
  whales: any[]
  news: any[]
  indicators: any[]
}

export interface CalibrationPoint {
  confidence_bin: number
  actual_accuracy: number
  prediction_count: number
}

export interface CalibrationData {
  ece: number
  brier_score: number
  reliability: number
  resolution: number
  uncertainty: number
  points: CalibrationPoint[]
}

export interface AdvisorRating {
  name: string
  weight: number
  accuracy: number
  consistency: number
  reliability_score: number
}

export function fetchTrustSummary(symbol: string = "GLOBAL"): Promise<TrustSummary> {
  return apiFetch<TrustSummary>(`/trust?symbol=${symbol}`)
}

export function fetchTrustHistory(limit: number = 50): Promise<TrustHistoryItem[]> {
  return apiFetch<TrustHistoryItem[]>(`/trust/history?limit=${limit}`)
}

export function fetchTrustEvidence(decisionId: string = ""): Promise<TrustEvidence> {
  return apiFetch<TrustEvidence>(`/trust/evidence?decision_id=${decisionId}`)
}

export function fetchTrustCalibration(): Promise<CalibrationData> {
  return apiFetch<CalibrationData>("/trust/calibration")
}

export function fetchTrustAdvisors(): Promise<AdvisorRating[]> {
  return apiFetch<AdvisorRating[]>("/trust/advisors")
}
