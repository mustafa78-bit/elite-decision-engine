import { apiFetch } from "./client"

export interface AIHealthResponse {
  status: string
  providers: Record<string, { connected: boolean; latency_ms: number; error: string | null }>
  ollo: {
    connected: boolean
    latency_ms: number
    error: string | null
  }
  evidence_engine: {
    available: boolean
    latest_report: string | null
  }
  timestamp: string
}

export function fetchAIHealth(): Promise<AIHealthResponse> {
  return apiFetch<AIHealthResponse>("/health/ai")
}
