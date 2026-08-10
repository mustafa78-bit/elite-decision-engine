import type { TradeIntelligence } from "../types/trade.ts";

interface Props {
  intelligence: TradeIntelligence | null | undefined;
}

export default function IntelligencePanel({ intelligence }: Props) {
  return (
    <div className="border border-gray-800 rounded bg-gray-900/50 px-3 py-2.5">
      <h3 className="text-[12px] font-semibold uppercase tracking-widest text-[var(--text-secondary)] mb-2">
        Intelligence
      </h3>
      {intelligence ? (
        <div className="space-y-3.5">
          <div className="text-center py-2">
            <p className="text-[11px] font-medium uppercase tracking-widest text-[var(--text-secondary)] mb-1">AI Council</p>
            <p className={`text-lg font-bold font-mono ${
              intelligence.decision === "APPROVE" ? "text-[var(--accent-green)]" :
              intelligence.decision === "REJECT" ? "text-[var(--accent-red)]" :
              "text-[var(--accent-yellow)]"
            }`}>
              {intelligence.decision}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[13px]">
            <span className="text-[var(--text-secondary)]">Confidence</span>
            <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">
              {(intelligence.confidence * 100).toFixed(0)}%
            </span>
            <span className="text-[var(--text-secondary)]">Trend</span>
            <span className={`text-right font-mono font-semibold tabular-nums ${
              intelligence.trend_score > 0.3 ? "text-[var(--accent-green)]" :
              intelligence.trend_score < -0.3 ? "text-[var(--accent-red)]" :
              "text-[var(--text-primary)]"
            }`}>
              {intelligence.trend_score > 0.3 ? "Bullish" :
               intelligence.trend_score < -0.3 ? "Bearish" : "Neutral"}
            </span>
            <span className="text-[var(--text-secondary)]">Risk</span>
            <span className={`text-right font-mono font-semibold tabular-nums ${
              intelligence.risk_score < 0.3 ? "text-[var(--accent-green)]" :
              intelligence.risk_score < 0.7 ? "text-[var(--accent-yellow)]" :
              "text-[var(--accent-red)]"
            }`}>
              {intelligence.risk_score < 0.3 ? "Low" :
               intelligence.risk_score < 0.7 ? "Medium" : "High"}
            </span>
          </div>
          <div className="border-t border-gray-800 pt-2.5">
            <p className="text-[11px] font-medium uppercase tracking-widest text-[var(--text-secondary)] mb-2">Decision Factors</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[12.5px]">
              <span className="text-[var(--text-secondary)]">Final Score</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.final_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">Trend</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.trend_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">Volume</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.volume_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">BTC</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.btc_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">MTF</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.mtf_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">Risk</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.risk_score.toFixed(1)}</span>
              <span className="text-[var(--text-secondary)]">RSI</span>
              <span className="text-right font-mono font-semibold tabular-nums text-[var(--text-primary)]">{intelligence.rsi.toFixed(0)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <span className="text-[24px] opacity-30 mb-2">◈</span>
          <p className="text-[13px] text-[var(--text-secondary)] font-mono">No intelligence available yet</p>
          <p className="text-[11px] text-[var(--text-muted)] mt-1 max-w-[200px]">
            AI insights will appear after the first completed analysis
          </p>
        </div>
      )}
    </div>
  );
}
