import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatUSD } from "../../lib/utils";

interface PnLPoint {
  label: string;
  value: number;
}

interface PnLTrendWidgetProps {
  data?: PnLPoint[];
  totalPnL?: number;
}

export function PnLTrendWidget({ data = [], totalPnL = 0 }: PnLTrendWidgetProps) {
  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>PnL Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-24 text-sm text-[var(--text-muted)]">
            No data
          </div>
        </CardContent>
      </Card>
    );
  }

  const values = data.map((d) => d.value);
  const maxVal = Math.max(...values.map(Math.abs), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>PnL Trend</CardTitle>
        <span
          className={`text-sm font-mono font-bold tabular-nums ${
            totalPnL >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
          }`}
        >
          {totalPnL >= 0 ? "+" : ""}
          {formatUSD(totalPnL)}
        </span>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-1 h-24">
          {data.map((d, i) => {
            const pct = Math.abs(d.value) / maxVal;
            const isPositive = d.value >= 0;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                <div
                  className="w-full rounded-t-sm transition-all"
                  style={{
                    height: `${Math.max(pct * 100, 2)}%`,
                    backgroundColor: isPositive ? "var(--accent-green)" : "var(--accent-red)",
                    opacity: 0.7 + pct * 0.3,
                  }}
                />
                <span className="text-[7px] font-mono text-[var(--text-muted)]">
                  {d.label}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
