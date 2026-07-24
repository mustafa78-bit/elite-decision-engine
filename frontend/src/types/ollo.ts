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

// Rich OLLO Message Architecture (Sprint 2A)
export interface OLLOAction {
  id: string
  label: string
  type: "navigate" | "execute_trade" | "dismiss" | "custom"
  payload?: Record<string, any>
}

export interface RichOLLOMessage {
  id: string
  sender: "user" | "ollo"
  timestamp: string

  // Rich details
  title?: string
  summary?: string
  reasoning?: string[]
  evidence?: {
    type: "technical" | "whale" | "macro" | "funding" | "news" | "portfolio" | "historical"
    description: string
    confidence?: number
  }[]
  confidence?: number // 0 - 100
  risk?: "LOW" | "MODERATE" | "HIGH" | "CRITICAL"
  actions?: OLLOAction[]

  // Plain text fallback / conversation text
  text?: string
}
