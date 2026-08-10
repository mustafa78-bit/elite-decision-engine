import { apiFetch } from "./client"

export interface AIHealthResponse {
  provider: string
  model: string
  current_mission_profile: string
  current_room: string
  ollo: {
    connected: boolean
    latency_ms: number
    error: string | null
  }
}

// /health/ai never existed as a backend route -- every call 404'd, so the
// "AI" subsystem indicator always showed OFFLINE regardless of whether the
// AI provider was actually reachable. /ollo/status is the real endpoint
// that already reports AI provider connectivity (as "ai_health").
export async function fetchAIHealth(): Promise<AIHealthResponse> {
  const status = await apiFetch<{
    provider: string
    model: string
    current_mission_profile: string
    current_room: string
    ai_health: { connected: boolean; latency_ms: number; error: string | null }
  }>("/ollo/status")
  return {
    provider: status.provider,
    model: status.model,
    current_mission_profile: status.current_mission_profile,
    current_room: status.current_room,
    ollo: status.ai_health,
  }
}
