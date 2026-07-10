import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface SentimentSource {
  source: string;
  score: number;
  label: string;
}

interface MarketSentimentWidgetProps {
  overall?: "BULLISH" | "BEARISH" | "NEUTRAL";
  score?: number;
  sources?: SentimentSource[];
}

export function MarketSentimentWidget({
  overall = "NEUTRAL",
  score = 50,
  sources = [],
}: MarketSentimentWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Market Sentiment</CardTitle>
        <Badge
          variant={
            overall === "BULLISH"
              ? "success"
              : overall === "BEARISH"
                ? "danger"
                : "warning"
          }
        >
          {overall}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-mono font-bold tabular-nums text-[var(--text-primary)]">
            {score.toFixed(0)}
          </span>
          <div className="flex-1 h-2 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-[var(--accent-red)] via-[var(--accent-yellow)] to-[var(--accent-green)] transition-all"
              style={{ width: `${score}%` }}
            />
          </div>
        </div>
        {sources.length > 0 && (
          <div className="space-y-1">
            {sources.map((s) => (
              <div key={s.source} className="flex items-center justify-between py-1">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {s.source}
                </span>
                <span className="text-[10px] font-mono tabular-nums text-[var(--text-primary)]">
                  {s.label}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
