import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Pattern {
  name: string;
  symbol: string;
  direction: "bullish" | "bearish";
  reliability: number;
  timeframe: string;
  description: string;
}

interface PatternRecognitionProps {
  patterns?: Pattern[];
}

export function PatternRecognition({
  patterns = [
    { name: "Bull Flag", symbol: "BTC/USDT", direction: "bullish", reliability: 82, timeframe: "1h", description: "Consolidation after strong upward move with decreasing volume" },
    { name: "Cup & Handle", symbol: "ETH/USDT", direction: "bullish", reliability: 76, timeframe: "4h", description: "Rounded bottom with slight pullback, potential breakout" },
    { name: "Double Top", symbol: "SOL/USDT", direction: "bearish", reliability: 68, timeframe: "1h", description: "Two failed attempts at resistance, volume declining" },
  ],
}: PatternRecognitionProps) {
  if (patterns.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Pattern Recognition</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No patterns detected</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Pattern Recognition</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {patterns.map((p) => (
          <div key={`${p.name}-${p.symbol}`} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] ${p.direction === "bullish" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {p.direction === "bullish" ? "▲" : "▼"}
                </span>
                <span className="text-[10px] font-mono font-medium text-[var(--text-primary)]">{p.name}</span>
                <Badge variant={p.direction === "bullish" ? "success" : "danger"} className="text-[8px]">{p.direction}</Badge>
              </div>
              <span className="text-[9px] font-mono text-[var(--text-muted)]">{p.reliability}% · {p.timeframe}</span>
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">{p.description}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
