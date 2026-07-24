import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface ModelStats {
  name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  trades: number;
}

interface ModelComparisonProps {
  models?: ModelStats[];
}

export function ModelComparison({
  models = [
    { name: "LSTM", accuracy: 68.2, precision: 72.1, recall: 65.4, f1Score: 68.6, trades: 342 },
    { name: "Transformer", accuracy: 71.5, precision: 74.8, recall: 69.2, f1Score: 71.9, trades: 298 },
    { name: "XGBoost", accuracy: 65.8, precision: 68.3, recall: 63.1, f1Score: 65.6, trades: 415 },
    { name: "CNN", accuracy: 67.1, precision: 70.5, recall: 64.8, f1Score: 67.5, trades: 267 },
  ],
}: ModelComparisonProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Model Comparison</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="px-3 py-1 border-b border-[var(--border-subtle)] flex text-[11px] font-mono text-[var(--text-muted)] uppercase tracking-wider">
          <span className="flex-[1.5]">Model</span>
          <span className="flex-[1] text-right">Acc</span>
          <span className="flex-[1] text-right">Prec</span>
          <span className="flex-[1] text-right">Recall</span>
          <span className="flex-[1] text-right">F1</span>
          <span className="flex-[1] text-right">Trades</span>
        </div>
        {models.map((m) => (
          <div key={m.name} className="flex items-center px-3 py-1.5 text-[12px] font-mono border-b border-[var(--border-subtle)] last:border-b-0 hover:bg-[var(--bg-hover)]">
            <span className="flex-[1.5] text-[var(--text-secondary)]">{m.name}</span>
            <span className="flex-[1] text-right tabular-nums">{m.accuracy.toFixed(1)}%</span>
            <span className="flex-[1] text-right tabular-nums">{m.precision.toFixed(1)}%</span>
            <span className="flex-[1] text-right tabular-nums">{m.recall.toFixed(1)}%</span>
            <span className="flex-[1] text-right tabular-nums font-bold text-[var(--accent-blue)]">{m.f1Score.toFixed(1)}</span>
            <span className="flex-[1] text-right text-[var(--text-muted)]">{m.trades}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
