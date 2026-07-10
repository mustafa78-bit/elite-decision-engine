import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface TFView {
  timeframe: string;
  trend: "bullish" | "bearish" | "neutral";
  strength: number;
  rsi: number;
  volume: "high" | "normal" | "low";
}

interface MultiTimeframeViewProps {
  symbol?: string;
  views?: TFView[];
}

export function MultiTimeframeView({
  symbol = "BTC/USDT",
  views = [
    { timeframe: "1m", trend: "bullish", strength: 65, rsi: 58, volume: "normal" },
    { timeframe: "5m", trend: "bullish", strength: 72, rsi: 62, volume: "high" },
    { timeframe: "15m", trend: "bullish", strength: 68, rsi: 60, volume: "normal" },
    { timeframe: "1h", trend: "bullish", strength: 75, rsi: 64, volume: "high" },
    { timeframe: "4h", trend: "neutral", strength: 52, rsi: 55, volume: "normal" },
    { timeframe: "1d", trend: "bullish", strength: 70, rsi: 61, volume: "normal" },
    { timeframe: "1w", trend: "neutral", strength: 48, rsi: 52, volume: "low" },
  ],
}: MultiTimeframeViewProps) {
  const bullishCount = views.filter((v) => v.trend === "bullish").length;
  const bearishCount = views.filter((v) => v.trend === "bearish").length;
  const consensus = bullishCount > bearishCount ? "BULLISH" : bearishCount > bullishCount ? "BEARISH" : "NEUTRAL";

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Multi-Timeframe</CardTitle>
          <Badge variant={consensus === "BULLISH" ? "success" : consensus === "BEARISH" ? "danger" : "warning"}>
            {consensus} {bullishCount}/{bearishCount}
          </Badge>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-3 py-1 border-b border-[var(--border-subtle)] flex text-[8px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          <span className="flex-[1.5]">TF</span>
          <span className="flex-[1.5]">Trend</span>
          <span className="flex-[1] text-right">Str</span>
          <span className="flex-[1] text-right">RSI</span>
          <span className="flex-[1] text-right">Vol</span>
        </div>
        {views.map((v) => (
          <div key={v.timeframe} className="flex items-center px-3 py-1 text-[10px] font-mono border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
            <span className="flex-[1.5] text-[var(--text-primary)]">{v.timeframe}</span>
            <span className={`flex-[1.5] ${v.trend === "bullish" ? "text-[var(--accent-green)]" : v.trend === "bearish" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}`}>
              {v.trend === "bullish" ? "▲" : v.trend === "bearish" ? "▼" : "◆"} {v.trend}
            </span>
            <span className="flex-[1] text-right text-[var(--text-secondary)] tabular-nums">{v.strength}</span>
            <span className={`flex-[1] text-right tabular-nums ${v.rsi >= 60 ? "text-[var(--accent-green)]" : v.rsi <= 40 ? "text-[var(--accent-red)]" : "text-[var(--text-muted)]"}`}>
              {v.rsi}
            </span>
            <span className="flex-[1] text-right">
              <span className={`w-1.5 h-1.5 rounded-full inline-block ${v.volume === "high" ? "bg-[var(--accent-green)]" : v.volume === "low" ? "bg-[var(--accent-red)]" : "bg-[var(--accent-yellow)]"}`} />
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
