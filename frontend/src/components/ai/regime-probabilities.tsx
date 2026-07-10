import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";

interface Regime {
  name: string;
  probability: number;
  color: string;
}

interface RegimeProbabilitiesProps {
  regimes?: Regime[];
  current?: string;
}

export function RegimeProbabilities({
  current = "Accumulation",
  regimes = [
    { name: "Accumulation", probability: 52, color: "bg-[var(--accent-blue)]" },
    { name: "Markup", probability: 18, color: "bg-[var(--accent-green)]" },
    { name: "Distribution", probability: 12, color: "bg-[var(--accent-red)]" },
    { name: "Markdown", probability: 8, color: "bg-[var(--accent-yellow)]" },
    { name: "Volatile", probability: 10, color: "bg-purple-500" },
  ],
}: RegimeProbabilitiesProps) {
  const totalProb = regimes.reduce((s, r) => s + r.probability, 0);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Regime Probabilities</CardTitle>
          <Badge variant="info">{current}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {totalProb > 0 && (
          <div className="flex h-2 rounded-full overflow-hidden">
            {regimes.map((r) => (
              <div key={r.name} className={r.color} style={{ width: `${(r.probability / totalProb) * 100}%` }} title={`${r.name}: ${r.probability}%`} />
            ))}
          </div>
        )}
        {regimes.map((r) => (
          <div key={r.name}>
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[10px] font-mono text-[var(--text-secondary)]">{r.name}</span>
              <span className="text-[10px] font-mono tabular-nums text-[var(--accent-blue)]">{r.probability}%</span>
            </div>
            <Progress
              value={r.probability}
              indicatorClassName={`h-full rounded-full ${r.color}`}
              className="h-1"
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
