export interface OLLOResponseSection {
  heading: string
  content: string
}

export interface OLLOResponse {
  text: string
  room: string
  timestamp: string
  provider: string
  model: string
  duration_ms: number
  tokens_in: number
  tokens_out: number
  sections: OLLOResponseSection[]
}

export interface OLLOBriefing {
  kind: string
  title: string
  text: string
  timestamp: string
  provider: string
  model: string
  duration_ms: number
  tokens_in: number
  tokens_out: number
}

export interface AIHealth {
  connected: boolean
  latency_ms: number
  error: string | null
}

export interface OLLOStatus {
  provider: string
  model: string
  current_mission_profile: string
  current_room: string
  ai_health: AIHealth
  memory: Record<string, unknown>
  available_rooms: string[]
}
