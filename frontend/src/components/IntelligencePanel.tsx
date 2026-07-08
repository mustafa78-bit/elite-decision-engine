import type { TradeIntelligence } from "../types/trade.ts";

interface Props {
  intelligence: TradeIntelligence;
}

function Row({ label, value, suffix }: { label: string; value: number | string; suffix?: string }) {
  return (
    <div className="flex justify-between py-1 border-b border-gray-900 last:border-0">
      <span className="text-gray-500 text-[11px]">{label}</span>
      <span className="tabular-nums text-gray-200">
        {value}
        {suffix && <span className="text-gray-500 ml-0.5">{suffix}</span>}
      </span>
    </div>
  );
}

export default function IntelligencePanel({ intelligence }: Props) {
  return (
    <div className="border border-gray-800 rounded bg-gray-900/50 px-3 py-2">
      <h3 className="text-[10px] uppercase tracking-widest text-gray-500 mb-2">
        Intelligence
      </h3>
      <Row label="Decision" value={intelligence.decision} />
      <Row label="Confidence" value={(intelligence.confidence * 100).toFixed(0)} suffix="%" />
      <Row label="Final Score" value={intelligence.final_score.toFixed(2)} />
      <Row label="Trend" value={intelligence.trend_score.toFixed(2)} />
      <Row label="Volume" value={intelligence.volume_score.toFixed(2)} />
      <Row label="BTC" value={intelligence.btc_score.toFixed(2)} />
      <Row label="MTF" value={intelligence.mtf_score.toFixed(2)} />
      <Row label="Risk" value={intelligence.risk_score.toFixed(2)} />
      <Row label="RSI" value={intelligence.rsi.toFixed(0)} />
    </div>
  );
}
