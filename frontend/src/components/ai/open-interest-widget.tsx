import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface OIData {
  symbol: string;
  oi: number;
  change24h: number;
  longShortRatio: number;
  volume24h: number;
}

interface OpenInterestWidgetProps {
  data?: OIData[];
}

export function OpenInterestWidget({ data = [] }: OpenInterestWidgetProps) {
  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Open Interest</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No OI data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          Open Interest
          <span className="text-[9px] font-mono text-[var(--text-muted)] ml-2">
            24h change
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {data.map((d) => (
            <div
              key={d.symbol}
              className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
            >
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-[var(--text-secondary)]">
                  {d.symbol}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[10px] font-mono tabular-nums text-[var(--text-primary)]">
                  ${(d.oi / 1_000_000_000).toFixed(2)}B
                </span>
                <span className={`text-[10px] font-mono tabular-nums ${d.change24h >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}`}>
                  {d.change24h >= 0 ? "+" : ""}{d.change24h.toFixed(1)}%
                </span>
                <Badge variant={d.longShortRatio > 1 ? "success" : "danger"}>
                  L/S: {d.longShortRatio.toFixed(2)}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
