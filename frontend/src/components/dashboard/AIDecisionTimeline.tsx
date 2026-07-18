import { useState } from "react";
import type { TradeIntelligence, TradeNotification } from "../../types/trade";

interface Props {
  notifications: TradeNotification[];
}

function DetailRow({ label, value, suffix }: { label: string; value: number | string; suffix?: string }) {
  return (
    <div className="flex justify-between py-0.5 text-[10px]">
      <span className="text-[var(--text-muted)]">{label}</span>
      <span className="font-mono tabular-nums text-[var(--text-primary)]">
        {value}{suffix && <span className="text-[var(--text-muted)] ml-0.5">{suffix}</span>}
      </span>
    </div>
  );
}

function DecisionDetail({ intel, timestamp }: { intel: TradeIntelligence; timestamp: string }) {
  const time = timestamp
    ? new Date(timestamp).toLocaleString("en-US", {
        hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
        month: "short", day: "numeric",
      })
    : "";
  return (
    <div className="pt-1.5 pb-1 border-t border-[var(--border-subtle)] mt-1.5 space-y-0.5">
      <DetailRow label="Decision" value={intel.decision} />
      <DetailRow label="Confidence" value={(intel.confidence * 100).toFixed(0)} suffix="%" />
      <DetailRow label="Final Score" value={intel.final_score.toFixed(1)} />
      <DetailRow label="Trend" value={intel.trend_score.toFixed(1)} />
      <DetailRow label="Volume" value={intel.volume_score.toFixed(1)} />
      <DetailRow label="BTC" value={intel.btc_score.toFixed(1)} />
      <DetailRow label="MTF" value={intel.mtf_score.toFixed(1)} />
      <DetailRow label="Risk" value={intel.risk_score.toFixed(1)} />
      <DetailRow label="RSI" value={intel.rsi.toFixed(0)} />
      <div className="text-[9px] text-[var(--text-muted)] opacity-50 pt-0.5">{time}</div>
    </div>
  );
}

export default function AIDecisionTimeline({ notifications }: Props) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  const decisions = notifications
    .filter((n) => n.payload.intelligence)
    .reverse()
    .slice(0, 5);

  if (decisions.length === 0) {
    return (
      <div className="border border-dashed border-[var(--border-subtle)] rounded px-3 py-4 text-center">
        <p className="text-[10px] text-[var(--text-muted)] font-mono">No decisions yet</p>
      </div>
    );
  }

  return (
    <div className="border border-[var(--border-subtle)] rounded px-3 py-2">
      <h3 className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Decision Timeline</h3>
      <div className="space-y-0.5">
        {decisions.map((n, i) => {
          const intel = n.payload.intelligence!;
          const time = n.timestamp
            ? new Date(n.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
            : "";
          const open = selectedIdx === i;
          return (
            <div key={i}>
              <button
                onClick={() => setSelectedIdx(open ? null : i)}
                className="w-full flex items-center justify-between text-[10px] font-mono hover:bg-[var(--bg-elevated)] rounded px-1 py-1 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                    intel.decision === "APPROVE" ? "bg-[var(--accent-green)]" :
                    intel.decision === "REJECT" ? "bg-[var(--accent-red)]" :
                    "bg-[var(--accent-yellow)]"
                  }`} />
                  <span className={
                    intel.decision === "APPROVE" ? "text-[var(--accent-green)]" :
                    intel.decision === "REJECT" ? "text-[var(--accent-red)]" :
                    "text-[var(--accent-yellow)]"
                  }>
                    {intel.decision}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[var(--text-muted)]">{(intel.confidence * 100).toFixed(0)}%</span>
                  <span className="text-[var(--text-muted)] opacity-50">{time}</span>
                </div>
              </button>
              {open && <DecisionDetail intel={intel} timestamp={n.timestamp} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
