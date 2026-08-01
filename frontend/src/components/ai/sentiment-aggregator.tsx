import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface SentimentSource {
  source: string;
  score: number;
  volume: number;
  direction: "positive" | "negative" | "neutral";
}

interface SentimentAggregatorProps {
  sources?: SentimentSource[];
  overallScore?: number;
}

export function SentimentAggregator({
  overallScore = 62,
  sources = [
    { source: "Twitter/X", score: 65, volume: 12400, direction: "positive" },
    { source: "Reddit", score: 58, volume: 3800, direction: "positive" },
    { source: "News", score: 72, volume: 420, direction: "positive" },
    { source: "Telegram", score: 55, volume: 2100, direction: "neutral" },
    { source: "Discord", score: 60, volume: 1800, direction: "positive" },
  ],
}: SentimentAggregatorProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Sentiment Aggregator</CardTitle>
          <Badge variant={overallScore > 60 ? "success" : overallScore > 40 ? "warning" : "danger"}>
            {overallScore}/100
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="flex h-3 rounded-full overflow-hidden">
          <div className="bg-[var(--accent-green)]" style={{ width: `${overallScore}%` }} />
          <div className="bg-[var(--accent-red)]" style={{ width: `${100 - overallScore}%` }} />
        </div>
        {sources.map((s) => (
          <div key={s.source}>
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`text-[10px] ${s.direction === "positive" ? "text-[var(--accent-green)]" : s.direction === "negative" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}`}>
                  {s.direction === "positive" ? "▲" : s.direction === "negative" ? "▼" : "◆"}
                </span>
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">{s.source}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-mono text-[var(--text-muted)]">{(s.volume / 1000).toFixed(1)}K</span>
                <span className={`text-[10px] font-mono tabular-nums ${s.score >= 60 ? "text-[var(--accent-green)]" : s.score >= 40 ? "text-[var(--accent-yellow)]" : "text-[var(--accent-red)]"}`}>
                  {s.score}%
                </span>
              </div>
            </div>
            <Progress
              value={s.score}
              indicatorClassName={`h-full rounded-full ${s.score >= 60 ? "bg-[var(--accent-green)]" : s.score >= 40 ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-red)]"}`}
              className="h-1"
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
