import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Anomaly {
  id: string;
  type: string;
  symbol: string;
  severity: "high" | "medium" | "low";
  description: string;
  time: string;
  value: string;
  expected: string;
}

interface AnomalyDetectionProps {
  anomalies?: Anomaly[];
}

export function AnomalyDetection({
  anomalies = [
    { id: "1", type: "Volume Spike", symbol: "BTC/USDT", severity: "high", description: "Volume 5.2x above 24h average", time: "2m ago", value: "52,400 BTC", expected: "10,100 BTC" },
    { id: "2", type: "Price Gap", symbol: "ETH/USDT", severity: "medium", description: "Price gap of 2.1% in 1 minute", time: "15m ago", value: "$2,245", expected: "$2,198" },
    { id: "3", type: "OI Spike", symbol: "SOL/USDT", severity: "medium", description: "Open interest increased 18% in 5m", time: "1h ago", value: "$2.8B", expected: "$2.4B" },
  ],
}: AnomalyDetectionProps) {
  if (anomalies.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Anomaly Detection</CardTitle></CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">No anomalies detected</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          Anomaly Detection
          <span className="text-[9px] font-mono text-[var(--text-muted)] ml-2">{anomalies.length} alerts</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1.5">
        {anomalies.map((a) => (
          <div key={a.id} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="flex items-center justify-between mb-0.5">
              <div className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${a.severity === "high" ? "bg-[var(--accent-red)]" : a.severity === "medium" ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"}`} />
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">{a.type}</span>
                <Badge variant={a.severity === "high" ? "danger" : a.severity === "medium" ? "warning" : "info"} className="text-[8px]">{a.severity}</Badge>
              </div>
              <span className="text-[8px] font-mono text-[var(--text-muted)]">{a.time}</span>
            </div>
            <div className="text-[9px] text-[var(--text-muted)] mb-0.5">{a.description}</div>
            <div className="flex gap-2 text-[9px] font-mono">
              <span className="text-[var(--accent-red)]">Actual: {a.value}</span>
              <span className="text-[var(--text-muted)]">Expected: {a.expected}</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
