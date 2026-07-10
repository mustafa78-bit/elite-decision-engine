import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { formatTime, formatCompact } from "../../lib/utils";

interface Signal {
  id: string;
  symbol: string;
  direction: "BUY" | "SELL" | "NEUTRAL";
  strength: number;
  strategy: string;
  price: number;
  timestamp: string;
}

interface SignalFeedProps {
  signals?: Signal[];
}

const directionBadge: Record<string, "success" | "danger" | "warning"> = {
  BUY: "success",
  SELL: "danger",
  NEUTRAL: "warning",
};

export function SignalFeed({ signals = [] }: SignalFeedProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Signal Feed</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {signals.length} signals
        </span>
      </CardHeader>
      <CardContent className="max-h-80 overflow-y-auto">
        {signals.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No signals available
          </div>
        ) : (
          <div className="space-y-1">
            {signals.slice(0, 10).map((s, i) => (
              <div key={s.id}>
                <div className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-medium text-[var(--text-primary)]">
                      {s.symbol}
                    </span>
                    <Badge variant={directionBadge[s.direction]}>
                      {s.direction}
                    </Badge>
                    <div className="h-4 w-16 rounded-sm bg-[var(--bg-elevated)] overflow-hidden">
                      <div
                        className={`h-full rounded-sm ${
                          s.direction === "BUY"
                            ? "bg-[var(--accent-green)]"
                            : s.direction === "SELL"
                              ? "bg-[var(--accent-red)]"
                              : "bg-[var(--accent-yellow)]"
                        }`}
                        style={{ width: `${s.strength * 10}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">
                    {formatTime(s.timestamp)}
                  </span>
                </div>
                <div className="flex justify-between text-[10px] font-mono text-[var(--text-muted)]">
                  <span>{s.strategy}</span>
                  <span>
                    {formatCompact(s.price)} | {s.strength.toFixed(1)}/10
                  </span>
                </div>
                {i < signals.length - 1 && i < 9 && (
                  <Separator className="my-0.5" />
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
