import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface LatencyPoint {
  label: string;
  value: number;
}

interface LatencyMonitorWidgetProps {
  currentLatency?: number;
  avgLatency?: number;
  maxLatency?: number;
  history?: LatencyPoint[];
}

export function LatencyMonitorWidget({
  currentLatency = 0,
  avgLatency = 0,
  maxLatency = 0,
  history = [],
}: LatencyMonitorWidgetProps) {
  const maxVal = Math.max(...history.map((h) => h.value), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Latency</CardTitle>
        <span
          className={`text-[10px] font-mono ${
            currentLatency < 50
              ? "text-[var(--accent-green)]"
              : currentLatency < 200
                ? "text-[var(--accent-yellow)]"
                : "text-[var(--accent-red)]"
          }`}
        >
          {currentLatency.toFixed(0)}ms
        </span>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center">
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {avgLatency.toFixed(0)}ms
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Avg</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {maxLatency.toFixed(0)}ms
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Max</div>
          </div>
          <div className="text-center">
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {currentLatency.toFixed(0)}ms
            </div>
            <div className="text-[9px] text-[var(--text-muted)]">Now</div>
          </div>
        </div>
        {history.length > 0 && (
          <div className="flex items-end gap-0.5 h-12">
            {history.map((h, i) => {
              const pct = h.value / maxVal;
              return (
                <div
                  key={i}
                  className="flex-1 rounded-t-sm"
                  style={{
                    height: `${Math.max(pct * 100, 5)}%`,
                    backgroundColor:
                      h.value < 50
                        ? "var(--accent-green)"
                        : h.value < 200
                          ? "var(--accent-yellow)"
                          : "var(--accent-red)",
                    opacity: 0.6 + pct * 0.4,
                  }}
                />
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
