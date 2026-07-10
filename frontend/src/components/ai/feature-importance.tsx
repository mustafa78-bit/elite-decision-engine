import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";

interface Feature {
  name: string;
  importance: number;
  category: string;
}

interface FeatureImportanceProps {
  features?: Feature[];
}

export function FeatureImportance({
  features = [
    { name: "RSI (14)", importance: 18.5, category: "Momentum" },
    { name: "Volume Profile", importance: 15.2, category: "Volume" },
    { name: "MACD", importance: 14.8, category: "Momentum" },
    { name: "Bollinger Width", importance: 12.1, category: "Volatility" },
    { name: "EMA Cross", importance: 11.5, category: "Trend" },
    { name: "Funding Rate", importance: 9.8, category: "Market" },
    { name: "Open Interest", importance: 8.2, category: "Market" },
    { name: "Whale Activity", importance: 5.9, category: "On-Chain" },
    { name: "Sentiment Score", importance: 4.0, category: "Sentiment" },
  ],
}: FeatureImportanceProps) {
  const maxImp = Math.max(...features.map((f) => f.importance), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Feature Importance</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {features.map((f) => (
          <div key={f.name}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">{f.name}</span>
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-mono text-[var(--text-muted)]">{f.category}</span>
                <span className="text-[10px] font-mono tabular-nums text-[var(--accent-blue)]">{f.importance}%</span>
              </div>
            </div>
            <Progress
              value={(f.importance / maxImp) * 100}
              indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]"
              className="h-1"
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
