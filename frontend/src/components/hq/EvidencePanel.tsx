import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import type { EvidenceReport, EvidenceItem, SourceTrace } from "../../types/evidence"

interface Props {
  report: EvidenceReport | null
  loading: boolean
  error: string | null
}

function qualityColor(q: string): string {
  switch (q) {
    case "HIGH": return "#22C55E"
    case "MEDIUM": return "#FACC15"
    case "LOW": return "#F97316"
    default: return "#64748B"
  }
}

function qualityLabel(q: string): string {
  switch (q) {
    case "HIGH": return "High Confidence"
    case "MEDIUM": return "Moderate"
    case "LOW": return "Low Confidence"
    default: return "Insufficient Data"
  }
}

function severityColor(s: string): string {
  switch (s) {
    case "HIGH": return "#EF4444"
    case "MEDIUM": return "#FACC15"
    case "LOW": return "#22C55E"
    default: return "#64748B"
  }
}

function GaugeBar({ value, label, color }: { value: number; label: string; color: string }) {
  const pct = Math.min(Math.max(value * 100, 0), 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[10px] font-mono">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span style={{ color }}>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-1 rounded-full bg-[var(--bg-deep)] overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>
    </div>
  )
}

function EvidenceItemRow({ item }: { item: EvidenceItem }) {
  return (
    <div className="flex items-start gap-2 py-1.5 border-b border-[var(--border-subtle)]/30 last:border-0">
      <span
        className="w-1.5 h-1.5 rounded-full mt-0.5 shrink-0"
        style={{ backgroundColor: item.supports_decision ? "#22C55E" : "#EF4444" }}
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-[10px] font-medium text-[var(--text-primary)] truncate">
            {item.title}
          </span>
          <span className="text-[8px] font-mono shrink-0 px-1 py-0.5 rounded" style={{ backgroundColor: `${severityColor(item.severity)}15`, color: severityColor(item.severity) }}>
            {item.severity}
          </span>
        </div>
        {item.description && (
          <p className="text-[9px] text-[var(--text-muted)] mt-0.5 leading-relaxed">{item.description}</p>
        )}
        <div className="flex items-center gap-2 mt-0.5">
          <span className="text-[8px] text-[var(--text-muted)] font-mono">{item.engine}</span>
          <span className="text-[8px] text-[var(--text-muted)]">·</span>
          <span className="text-[8px] text-[var(--text-muted)] font-mono">{item.category}</span>
          <span className="text-[8px] text-[var(--text-muted)]">·</span>
          <span className="text-[8px] text-[var(--text-muted)] font-mono">{(item.confidence * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  )
}

function SourceRow({ source }: { source: SourceTrace }) {
  return (
    <div className="flex items-start gap-2 py-1 text-[9px] font-mono">
      <span className="w-1 h-1 rounded-full mt-1 bg-[var(--text-muted)] shrink-0" />
      <div>
        <span className="text-[var(--text-secondary)]">{source.module} v{source.module_version}</span>
        <span className="text-[var(--text-muted)]"> · {source.component}</span>
      </div>
    </div>
  )
}

export default function EvidencePanel({ report, loading, error }: Props) {
  const [showReasoning, setShowReasoning] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const [showContradicting, setShowContradicting] = useState(true)
  const [showSupporting, setShowSupporting] = useState(false)

  if (loading) {
    return (
      <div className="glass-card p-5 space-y-4">
        <div className="h-3 skeleton-pulse w-1/3" />
        <div className="h-2 skeleton-pulse w-full" />
        <div className="h-2 skeleton-pulse w-3/4" />
        <div className="space-y-2">
          <div className="h-1 skeleton-pulse w-full" />
          <div className="h-1 skeleton-pulse w-full" />
          <div className="h-1 skeleton-pulse w-full" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-red)]" />
          <span className="text-[10px] font-medium text-[var(--accent-red)] uppercase tracking-[0.1em]">Evidence Offline</span>
        </div>
        <p className="text-[11px] text-[var(--text-muted)]">{error}</p>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)]" />
          <span className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">No Evidence Available</span>
        </div>
        <p className="text-[11px] text-[var(--text-muted)]">Awaiting first evidence briefing from the engines.</p>
      </div>
    )
  }

  const conflicts = report.contradicting_evidence.length
  const conflictLevel = conflicts === 0 ? "None" : conflicts <= 2 ? "Low" : conflicts <= 5 ? "Medium" : "High"
  const conflictColor = conflicts === 0 ? "#22C55E" : conflicts <= 2 ? "#FACC15" : conflicts <= 5 ? "#F97316" : "#EF4444"
  const supporting = report.supporting_evidence.length

  return (
    <div className="glass-card p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: qualityColor(report.decision_quality) }} />
          <span className="text-[10px] font-medium uppercase tracking-[0.1em]" style={{ color: qualityColor(report.decision_quality) }}>
            {qualityLabel(report.decision_quality)}
          </span>
        </div>
        <span className="text-[9px] font-mono text-[var(--text-muted)]">
          ID: {report.decision_id.slice(0, 8)}
        </span>
      </div>

      {/* Recommendation */}
      <div>
        <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-1">Decision</div>
        <p className="text-sm font-semibold text-[var(--text-primary)] leading-snug">{report.recommendation || "No active recommendation"}</p>
      </div>

      {/* Gauges */}
      <div className="space-y-2.5">
        <GaugeBar value={report.decision_confidence} label="Decision Confidence" color={qualityColor(report.decision_quality)} />
        <GaugeBar value={report.evidence_strength} label="Evidence Strength" color="#3B82F6" />
        <GaugeBar value={report.explainability} label="Explainability" color="#8B5CF6" />
      </div>

      {/* Conflict + Evidence counts */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-[var(--bg-deep)] rounded-lg p-2.5">
          <div className="text-[8px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">Conflict</div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: conflictColor }} />
            <span className="text-[10px] font-mono" style={{ color: conflictColor }}>{conflictLevel}</span>
          </div>
          <div className="text-[8px] text-[var(--text-muted)]">{conflicts} item{conflicts !== 1 ? 's' : ''}</div>
        </div>
        <div className="bg-[var(--bg-deep)] rounded-lg p-2.5">
          <div className="text-[8px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">Supporting</div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]" />
            <span className="text-[10px] font-mono text-[#22C55E]">{supporting}</span>
          </div>
          <div className="text-[8px] text-[var(--text-muted)]">evidence items</div>
        </div>
        <div className="bg-[var(--bg-deep)] rounded-lg p-2.5">
          <div className="text-[8px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">Warnings</div>
          <div className="flex items-center gap-1 mt-0.5">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: report.warnings.length > 0 ? "#F97316" : "#22C55E" }} />
            <span className="text-[10px] font-mono" style={{ color: report.warnings.length > 0 ? "#F97316" : "#22C55E" }}>
              {report.warnings.length}
            </span>
          </div>
          <div className="text-[8px] text-[var(--text-muted)]">mission alerts</div>
        </div>
      </div>

      {/* Contradicting Evidence — always visible */}
      {conflicts > 0 && (
        <div>
          <button
            onClick={() => setShowContradicting(!showContradicting)}
            className="flex items-center gap-2 w-full text-left"
            aria-expanded={showContradicting}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444]" />
            <span className="text-[9px] font-medium text-[#EF4444] uppercase tracking-[0.1em]">
              Contradicting Evidence ({conflicts})
            </span>
            <span className="ml-auto text-[var(--text-muted)] text-[9px]">{showContradicting ? "▲" : "▼"}</span>
          </button>
          <AnimatePresence initial={false}>
            {showContradicting && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-2 space-y-0 max-h-[200px] overflow-y-auto">
                  {report.contradicting_evidence.map((item) => (
                    <EvidenceItemRow key={item.id} item={item} />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Summary */}
      {report.summary && (
        <div>
          <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-1">Summary</div>
          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">{report.summary}</p>
        </div>
      )}

      {/* Reasoning — expandable */}
      {report.reasoning.length > 0 && (
        <div>
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className="flex items-center gap-2 w-full text-left"
            aria-expanded={showReasoning}
          >
            <span className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">
              Reasoning ({report.reasoning.length})
            </span>
            <span className="ml-auto text-[var(--text-muted)] text-[9px]">{showReasoning ? "▲" : "▼"}</span>
          </button>
          <AnimatePresence initial={false}>
            {showReasoning && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <ul className="mt-2 space-y-1">
                  {report.reasoning.map((r, i) => (
                    <li key={i} className="text-[10px] text-[var(--text-secondary)] leading-relaxed flex items-start gap-1.5">
                      <span className="text-[var(--accent-blue)] mt-0.5 shrink-0">{i + 1}.</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Supporting Evidence — expandable */}
      {report.supporting_evidence.length > 0 && (
        <div>
          <button
            onClick={() => setShowSupporting(!showSupporting)}
            className="flex items-center gap-2 w-full text-left"
            aria-expanded={showSupporting}
          >
            <span className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">
              Supporting Evidence ({supporting})
            </span>
            <span className="ml-auto text-[var(--text-muted)] text-[9px]">{showSupporting ? "▲" : "▼"}</span>
          </button>
          <AnimatePresence initial={false}>
            {showSupporting && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-2 space-y-0 max-h-[200px] overflow-y-auto">
                  {report.supporting_evidence.map((item) => (
                    <EvidenceItemRow key={item.id} item={item} />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Timeline */}
      {report.timeline.length > 0 && (
        <div>
          <div className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em] mb-2">Timeline</div>
          <div className="space-y-1 max-h-[140px] overflow-y-auto">
            {report.timeline.slice(-6).map((item) => (
              <div key={item.id} className="flex items-start gap-2 text-[10px]">
                <span
                  className="w-1 h-1 rounded-full mt-1 shrink-0"
                  style={{ backgroundColor: item.supports_decision ? "#22C55E" : "#EF4444" }}
                />
                <div className="min-w-0 flex-1">
                  <div className="text-[var(--text-primary)] truncate">{item.title}</div>
                  <div className="text-[var(--text-muted)] text-[9px]">{item.engine} · {item.category}</div>
                </div>
                <span className="text-[8px] font-mono shrink-0 px-1 rounded" style={{ backgroundColor: `${severityColor(item.severity)}15`, color: severityColor(item.severity) }}>
                  {item.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sources — expandable */}
      {report.sources.length > 0 && (
        <div>
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-2 w-full text-left"
            aria-expanded={showSources}
          >
            <span className="text-[9px] font-medium text-[var(--text-muted)] uppercase tracking-[0.1em]">
              Sources ({report.sources.length})
            </span>
            <span className="ml-auto text-[var(--text-muted)] text-[9px]">{showSources ? "▲" : "▼"}</span>
          </button>
          <AnimatePresence initial={false}>
            {showSources && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="mt-1 space-y-0">
                  {report.sources.map((source, i) => (
                    <SourceRow key={i} source={source} />
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Timestamp */}
      <div className="text-[8px] text-[var(--text-muted)] font-mono text-right">
        {new Date(report.created_at).toLocaleString()}
      </div>
    </div>
  )
}
