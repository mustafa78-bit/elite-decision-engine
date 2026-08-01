export interface SourceTrace {
  module: string
  module_version: string
  component: string
  input_keys: string[]
  output_keys: string[]
  timestamp: string
}

export interface EvidenceItem {
  id: string
  title: string
  description: string
  engine: string
  category: string
  severity: string
  confidence: number
  weight: number
  supports_decision: boolean
  metadata: Record<string, unknown>
  source: SourceTrace | null
  timestamp: string
  version: string
}

export interface EvidenceReport {
  recommendation: string
  decision_confidence: number
  evidence_strength: number
  explainability: number
  decision_quality: string
  summary: string
  reasoning: string[]
  supporting_evidence: EvidenceItem[]
  contradicting_evidence: EvidenceItem[]
  warnings: string[]
  risk_notes: string[]
  timeline: EvidenceItem[]
  sources: SourceTrace[]
  decision_id: string
  created_at: string
}

export interface TimelineEvent {
  time: string
  timestamp: string
  title: string
  description: string
  engine: string
  category: string
  supports_decision: boolean
  severity: string
}

export interface TimelineResponse {
  decision_id: string
  events: TimelineEvent[]
}
