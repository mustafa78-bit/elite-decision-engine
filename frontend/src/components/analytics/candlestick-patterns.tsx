import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface CandlePattern {
  name: string;
  symbol: string;
  direction: "bullish" | "bearish" | "neutral";
  reliability: number;
  timeframe: string;
}

interface CandlestickPatternsProps {
  patterns?: CandlePattern[];
}

export function CandlestickPatterns({
  patterns = [
    { name: "Hammer", symbol: "BTC/USDT", direction: "bullish", reliability: 75, timeframe: "1h" },
    { name: "Engulfing", symbol: "ETH/USDT", direction: "bullish", reliability: 80, timeframe: "4h" },
    { name: "Doji", symbol: "SOL/USDT", direction: "neutral", reliability: 45, timeframe: "1h" },
    { name: "Shooting Star", symbol: "AVAX/USDT", direction: "bearish", reliability: 70, timeframe: "30m" },
  ],
}: CandlestickPatternsProps) {
  if (patterns.length === 0) {
    return (
      <Card>
        <CardHeader><CardTitle>Candlestick Patterns</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No patterns detected</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Candlestick Patterns</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {patterns.map((p) => (
          <div key={`${p.name}-${p.symbol}`} className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[10px] font-mono">
            <div className="flex items-center gap-1.5">
              <span className={`text-[10px] ${p.direction === "bullish" ? "text-[var(--accent-green)]" : p.direction === "bearish" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}`}>
                {p.direction === "bullish" ? "▲" : p.direction === "bearish" ? "▼" : "◆"}
              </span>
              <span className="text-[var(--text-primary)]">{p.name}</span>
              <Badge variant={p.direction === "bullish" ? "success" : p.direction === "bearish" ? "danger" : "warning"} className="text-[8px]">{p.direction}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[var(--text-muted)]">{p.symbol}</span>
              <span className="text-[var(--text-muted)]">{p.timeframe}</span>
              <span className="text-[var(--accent-blue)]">{p.reliability}%</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
