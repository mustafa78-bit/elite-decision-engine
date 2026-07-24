import type { RegimeData } from "../../api/regime";

interface Props {
  data: RegimeData;
}

const TREND_COLORS: Record<string, string> = {
  BULLISH: "text-green-400",
  BEARISH: "text-red-400",
  NEUTRAL: "text-yellow-400",
};

const REGIME_COLORS: Record<string, string> = {
  TREND: "text-green-400",
  DOWNTREND: "text-red-400",
  RANGE: "text-yellow-400",
  DEAD: "text-[var(--text-muted)]",
};

const VOL_COLORS: Record<string, string> = {
  LOW: "text-blue-400",
  NORMAL: "text-[var(--text-secondary)]",
  HIGH: "text-red-400",
};

export default function RegimePanel({ data }: Props) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded p-4">
      <h3 className="text-[12px] uppercase tracking-widest text-[var(--text-muted)] mb-3">
        Market Regime
      </h3>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Regime</div>
          <div className={`font-semibold ${REGIME_COLORS[data.regime] || "text-[var(--text-primary)]"}`}>
            {data.regime}
          </div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Trend</div>
          <div className={`font-semibold ${TREND_COLORS[data.trend] || "text-[var(--text-primary)]"}`}>
            {data.trend}
          </div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">Volatility</div>
          <div className={`font-semibold ${VOL_COLORS[data.volatility_state] || "text-[var(--text-primary)]"}`}>
            {data.volatility_state} ({(data.volatility * 100).toFixed(2)}%)
          </div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">BTC Health</div>
          <div className="text-[var(--text-primary)] font-semibold tabular-nums">
            {(data.btc_health * 100).toFixed(0)}%
          </div>
        </div>
        <div>
          <div className="text-[var(--text-muted)] text-[12px] uppercase tracking-wider">RSI</div>
          <div className="text-[var(--text-primary)] font-semibold tabular-nums">{data.rsi}</div>
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-gray-800 text-[12px] text-[var(--text-muted)]">
        <span className="text-[var(--text-muted)]">EMA </span>
        <span className="tabular-nums">20={data.ema20} 50={data.ema50} 200={data.ema200}</span>
      </div>
    </div>
  );
}
