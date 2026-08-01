import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface VolatilityPoint {
  label: string;
  value: number;
}

interface VolatilityChartWidgetProps {
  data?: VolatilityPoint[];
  currentVol?: number;
}

export function VolatilityChartWidget({ data = [], currentVol = 0 }: VolatilityChartWidgetProps) {
  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Volatility</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-sm text-[var(--text-muted)]">
            No volatility data
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxVal = Math.max(...data.map((d) => d.value), 0.01);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Volatility</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          Current: {(currentVol * 100).toFixed(1)}%
        </span>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-1 h-32">
          {data.map((d, i) => {
            const pct = d.value / maxVal;
            const color =
              d.value < maxVal * 0.3
                ? "var(--accent-green)"
                : d.value < maxVal * 0.6
                  ? "var(--accent-yellow)"
                  : "var(--accent-red)";
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                <div
                  className="w-full rounded-t-sm transition-all"
                  style={{
                    height: `${Math.max(pct * 100, 3)}%`,
                    backgroundColor: color,
                    opacity: 0.4 + pct * 0.4,
                  }}
                />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
