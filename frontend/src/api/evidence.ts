import { apiFetch } from "./client"
import type { EvidenceReport, TimelineResponse } from "../types/evidence"

export function fetchLatestEvidence(): Promise<EvidenceReport> {
  return apiFetch<EvidenceReport>("/evidence/latest")
}

export function fetchEvidence(decisionId: string): Promise<EvidenceReport> {
  return apiFetch<EvidenceReport>(`/evidence/${decisionId}`)
}

export function fetchTimeline(decisionId: string): Promise<TimelineResponse> {
  return apiFetch<TimelineResponse>(`/evidence/timeline/${decisionId}`)
}
