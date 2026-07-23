import type { TradeIntelligence } from "../types/trade.ts";

interface Props {
  intelligence: TradeIntelligence | null | undefined;
}

export default function IntelligencePanel({ intelligence }: Props) {
  return (
    <div className="border border-gray-800 rounded bg-gray-900/50 px-3 py-2">
      <h3 className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">
        Intelligence
      </h3>
      {intelligence ? (
        <div className="space-y-3">
          <div className="text-center py-2">
            <p className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] mb-1">AI Council</p>
            <p className={`text-sm font-semibold font-mono ${
              intelligence.decision === "APPROVE" ? "text-[var(--accent-green)]" :
              intelligence.decision === "REJECT" ? "text-[var(--accent-red)]" :
              "text-[var(--accent-yellow)]"
            }`}>
              {intelligence.decision}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-[10px]">
            <span className="text-[var(--text-muted)]">Confidence</span>
            <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">
              {(intelligence.confidence * 100).toFixed(0)}%
            </span>
            <span className="text-[var(--text-muted)]">Trend</span>
            <span className={`text-right font-mono tabular-nums ${
              intelligence.trend_score > 0.3 ? "text-[var(--accent-green)]" :
              intelligence.trend_score < -0.3 ? "text-[var(--accent-red)]" :
              "text-[var(--text-muted)]"
            }`}>
              {intelligence.trend_score > 0.3 ? "Bullish" :
               intelligence.trend_score < -0.3 ? "Bearish" : "Neutral"}
            </span>
            <span className="text-[var(--text-muted)]">Risk</span>
            <span className={`text-right font-mono tabular-nums ${
              intelligence.risk_score < 0.3 ? "text-[var(--accent-green)]" :
              intelligence.risk_score < 0.7 ? "text-[var(--accent-yellow)]" :
              "text-[var(--accent-red)]"
            }`}>
              {intelligence.risk_score < 0.3 ? "Low" :
               intelligence.risk_score < 0.7 ? "Medium" : "High"}
            </span>
          </div>
          <div className="border-t border-gray-800 pt-2">
            <p className="text-[9px] uppercase tracking-widest text-[var(--text-muted)] mb-1.5">Decision Factors</p>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[10px]">
              <span className="text-[var(--text-muted)]">Final Score</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.final_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">Trend</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.trend_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">Volume</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.volume_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">BTC</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.btc_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">MTF</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.mtf_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">Risk</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.risk_score.toFixed(1)}</span>
              <span className="text-[var(--text-muted)]">RSI</span>
              <span className="text-right font-mono tabular-nums text-[var(--text-primary)]">{intelligence.rsi.toFixed(0)}</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-6 text-center">
          <span className="text-[20px] opacity-20 mb-2">◈</span>
          <p className="text-[11px] text-[var(--text-muted)] font-mono">No intelligence available yet</p>
          <p className="text-[9px] text-[var(--text-muted)]  mt-1 max-w-[180px]">
            AI insights will appear after the first completed analysis
          </p>
        </div>
      )}
    </div>
  );
}
