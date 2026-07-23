import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Pause,
  Percent,
  ArrowUpRight
} from "lucide-react";
import type { RichOLLOMessage } from "../../types/ollo";

interface Props {
  message: RichOLLOMessage;
  onAction?: (actionId: string, actionType: string, payload?: any) => void;
}

export function DecisionExplanationCard({ message, onAction }: Props) {
  const { title, summary, reasoning, evidence, confidence, risk, actions } = message;

  // Determine decision type from title/summary
  const decisionType = (title || "").toUpperCase();
  const isBuy = decisionType.includes("BUY") || decisionType.includes("LONG");
  const isSell = decisionType.includes("SELL") || decisionType.includes("SHORT");

  // Style attributes based on decision
  const badgeColor = isBuy
    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
    : isSell
    ? "bg-red-500/10 border-red-500/20 text-red-400"
    : "bg-amber-500/10 border-amber-500/20 text-amber-400";

  const glowColor = isBuy
    ? "shadow-[0_0_15px_rgba(16,185,129,0.15)]"
    : isSell
    ? "shadow-[0_0_15px_rgba(239,68,68,0.15)]"
    : "shadow-[0_0_15px_rgba(245,158,11,0.15)]";

  const icon = isBuy ? (
    <TrendingUp className="w-5 h-5 text-emerald-400 animate-pulse" />
  ) : isSell ? (
    <TrendingDown className="w-5 h-5 text-red-400 animate-pulse" />
  ) : (
    <Pause className="w-5 h-5 text-amber-400 animate-pulse" />
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -12 }}
      className={`rounded-xl border border-[var(--border-subtle)] bg-[#101A2E] p-4 text-[var(--text-primary)] transition-all hover:border-[var(--border-default)] ${glowColor}`}
    >
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-1.5 rounded-lg border ${badgeColor}`}>
            {icon}
          </div>
          <div>
            <div className="text-xs font-mono text-[var(--text-muted)] tracking-wider uppercase">
              AI Decision Core
            </div>
            <h4 className="text-sm font-bold tracking-tight text-[var(--text-primary)]">
              {title || "AI Evaluation"}
            </h4>
          </div>
        </div>

        {/* Confidence Badge */}
        {confidence !== undefined && (
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-mono text-[var(--text-muted)] tracking-wider uppercase">
              Confidence
            </span>
            <div className="flex items-center gap-1 font-mono font-semibold text-sm text-[var(--accent-blue)]">
              <Percent className="w-3.5 h-3.5" />
              <span>{confidence}%</span>
            </div>
          </div>
        )}
      </div>

      {/* Summary Description */}
      {summary && (
        <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-3 font-mono">
          {summary}
        </p>
      )}

      {/* Reasoning (Checklist / Why list) */}
      {reasoning && reasoning.length > 0 && (
        <div className="space-y-1.5 mb-3.5">
          <div className="text-[10px] font-mono text-[var(--text-muted)] tracking-wider uppercase mb-1">
            ✓ REASONING & TRIGGERS
          </div>
          <div className="grid grid-cols-1 gap-1.5">
            {reasoning.map((reason, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 bg-[#162338]/60 border border-[#263956]/30 rounded-lg p-2 text-xs font-mono text-[var(--text-secondary)]"
              >
                <span className={isBuy ? "text-emerald-400 font-bold" : isSell ? "text-red-400 font-bold" : "text-amber-400 font-bold"}>
                  ✓
                </span>
                <span>{reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence & Analytics Section */}
      {evidence && evidence.length > 0 && (
        <div className="space-y-1.5 mb-3.5">
          <div className="text-[10px] font-mono text-[var(--text-muted)] tracking-wider uppercase mb-1">
            Supporting Evidence
          </div>
          <div className="space-y-1">
            {evidence.map((ev, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between rounded-md bg-[#162338]/40 px-2 py-1.5 border border-[#263956]/20"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase bg-[#162338] border border-[#263956] px-1.5 py-0.5 rounded text-[var(--text-muted)]">
                    {ev.type}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)] font-mono truncate max-w-[180px]">
                    {ev.description}
                  </span>
                </div>
                {ev.confidence !== undefined && (
                  <span className="text-[10px] font-mono text-[var(--accent-blue)]">
                    {ev.confidence}%
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk and expected RR */}
      {risk && (
        <div className="grid grid-cols-2 gap-2 bg-[#162338]/80 border border-[#263956] rounded-lg p-2.5 mb-3.5">
          <div className="flex flex-col">
            <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
              Risk Assessment
            </span>
            <span className={`text-xs font-bold font-mono uppercase ${
              risk === "LOW" ? "text-emerald-400" : risk === "MODERATE" ? "text-amber-400" : "text-red-400"
            }`}>
              {risk}
            </span>
          </div>
          <div className="flex flex-col border-l border-[#263956] pl-2.5">
            <span className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
              Expected R:R
            </span>
            <span className="text-xs font-bold font-mono text-[var(--accent-blue)]">
              {isBuy ? "4.3x" : isSell ? "3.8x" : "N/A"}
            </span>
          </div>
        </div>
      )}

      {/* Interactive Actions Panel */}
      {actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-[var(--border-subtle)]">
          {actions.map((act) => (
            <button
              key={act.id}
              onClick={() => onAction?.(act.id, act.type, act.payload)}
              className="flex-1 min-w-[80px] flex items-center justify-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/85 text-white text-xs font-mono font-medium transition-all shadow-[0_2px_4px_rgba(30,58,138,0.3)] hover:translate-y-[-1px] active:translate-y-[0px]"
            >
              <span>{act.label}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          ))}
        </div>
      )}
    </motion.div>
  );
}
