import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface ModelResult {
  name: string;
  prediction: string;
  confidence: number;
  weight: number;
}

interface ModelEnsembleProps {
  symbol?: string;
  models?: ModelResult[];
  consensus?: string;
}

export function ModelEnsemble({
  symbol = "BTC/USDT",
  models = [
    { name: "LSTM", prediction: "BULLISH", confidence: 82, weight: 0.30 },
    { name: "Transformer", prediction: "BULLISH", confidence: 76, weight: 0.25 },
    { name: "XGBoost", prediction: "NEUTRAL", confidence: 65, weight: 0.20 },
    { name: "CNN", prediction: "BULLISH", confidence: 70, weight: 0.15 },
    { name: "Ensemble RF", prediction: "BULLISH", confidence: 78, weight: 0.10 },
  ],
  consensus = "BULLISH",
}: ModelEnsembleProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Model Ensemble</CardTitle>
          <Badge variant={consensus === "BULLISH" ? "success" : consensus === "BEARISH" ? "danger" : "warning"}>
            {consensus}
          </Badge>
        </div>
        <span className="text-[12px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-2">
        {models.map((m) => (
          <div key={m.name}>
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className="text-[12px] font-mono text-[var(--text-secondary)]">{m.name}</span>
                <Badge variant={m.prediction === "BULLISH" ? "success" : m.prediction === "BEARISH" ? "danger" : "warning"} className="text-[11px]">{m.prediction}</Badge>
              </div>
              <div className="flex items-center gap-1">
                <span className="text-[12px] font-mono tabular-nums text-[var(--accent-blue)]">{m.confidence}%</span>
                <span className="text-[11px] font-mono text-[var(--text-muted)]">w:{(m.weight * 100).toFixed(0)}%</span>
              </div>
            </div>
            <Progress value={m.confidence} indicatorClassName="h-full rounded-full bg-[var(--accent-blue)]" className="h-1" />
          </div>
        ))}
        <div className="pt-2 border-t border-[var(--border-subtle)] text-center">
          <span className="text-[12px] font-mono text-[var(--text-muted)]">{models.filter((m) => m.prediction === consensus).length}/{models.length} models agree</span>
        </div>
      </CardContent>
    </Card>
  );
}
