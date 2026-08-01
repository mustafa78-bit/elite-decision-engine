import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface AISummaryCardProps {
  symbol?: string;
  summary?: string;
  confidence?: number;
  direction?: "bullish" | "bearish" | "neutral";
  keyLevels?: { support: number; resistance: number };
  timeframe?: string;
}

export function AISummaryCard({
  symbol = "BTC/USDT",
  summary = "BTC/USDT shows strong bullish momentum with above-average volume. RSI at 62 suggests room for further upside. Key resistance at $43,200 with support at $41,500. Market regime is trending bullish.",
  confidence = 76,
  direction = "bullish",
  keyLevels = { support: 41500, resistance: 43200 },
  timeframe = "4h",
}: AISummaryCardProps) {
  return (
    <Card className="h-full" variant="elevated">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle>AI Summary</CardTitle>
            <span className="text-[9px] font-mono text-[var(--text-muted)]">
              {symbol} · {timeframe}
            </span>
          </div>
          <Badge variant={direction === "bullish" ? "success" : direction === "bearish" ? "danger" : "warning"}>
            {direction?.toUpperCase()} {confidence}%
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed">
          {summary}
        </p>
        {keyLevels && (
          <div className="flex gap-4 mt-3 pt-3 border-t border-[var(--border-subtle)]">
            <div>
              <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                Support
              </div>
              <div className="text-[11px] font-mono text-[var(--accent-green)] tabular-nums">
                ${keyLevels.support.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                Resistance
              </div>
              <div className="text-[11px] font-mono text-[var(--accent-red)] tabular-nums">
                ${keyLevels.resistance.toLocaleString()}
              </div>
            </div>
            <div>
              <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
                Confidence
              </div>
              <div className="text-[11px] font-mono text-[var(--accent-blue)]">
                {confidence}/100
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
