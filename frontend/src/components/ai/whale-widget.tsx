import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface WhaleActivity {
  symbol: string;
  type: "buy" | "sell" | "transfer";
  amount: number;
  usdValue: number;
  time: string;
  exchange: string;
}

interface WhaleWidgetProps {
  activities?: WhaleActivity[];
}

export function WhaleWidget({ activities = [] }: WhaleWidgetProps) {
  if (activities.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Whale Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No whale activity detected
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          Whale Activity
          <span className="text-[12px] font-mono text-[var(--text-muted)] ml-2">
            Last 24h
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {activities.map((a) => (
            <div
              key={`${a.symbol}-${a.time}`}
              className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
            >
              <div className="flex items-center gap-2">
                <span className={`text-[12px] ${a.type === "buy" ? "text-[var(--accent-green)]" : a.type === "sell" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}`}>
                  {a.type === "buy" ? "▲" : a.type === "sell" ? "▼" : "◆"}
                </span>
                <div>
                  <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                    {a.symbol}
                  </span>
                  <span className="text-[12px] font-mono text-[var(--text-muted)] ml-1">
                    {a.exchange}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[12px] font-mono tabular-nums text-[var(--text-primary)]">
                  ${(a.usdValue / 1_000_000).toFixed(1)}M
                </span>
                <Badge variant={a.type === "buy" ? "success" : a.type === "sell" ? "danger" : "warning"}>
                  {a.type}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
