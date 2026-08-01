import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface MiniPnLPoint {
  value: number;
}

interface MiniPnLChartWidgetProps {
  data?: MiniPnLPoint[];
  label?: string;
}

export function MiniPnLChartWidget({ data = [], label = "PnL" }: MiniPnLChartWidgetProps) {
  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>{label}</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-16 text-sm text-[var(--text-muted)]">
            No data
          </div>
        </CardContent>
      </Card>
    );
  }

  const values = data.map((d) => d.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <svg className="w-full h-16" viewBox={`0 0 ${data.length * 10} 64`} preserveAspectRatio="none">
          <polyline
            fill="none"
            stroke="var(--accent-blue)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity="0.8"
            points={data
              .map((d, i) => {
                const x = i * 10 + 5;
                const y = 58 - ((d.value - min) / range) * 48;
                return `${x},${y}`;
              })
              .join(" ")}
          />
          <polyline
            fill="url(#pnl-gradient)"
            opacity="0.15"
            points={`0,58 ${data
              .map((d, i) => {
                const x = i * 10 + 5;
                const y = 58 - ((d.value - min) / range) * 48;
                return `${x},${y}`;
              })
              .join(" ")} ${data.length * 10 - 5},58`}
          />
          <defs>
            <linearGradient id="pnl-gradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-blue)" />
              <stop offset="100%" stopColor="var(--accent-blue)" stopOpacity="0" />
            </linearGradient>
          </defs>
        </svg>
      </CardContent>
    </Card>
  );
}
