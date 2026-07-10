import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchRegime } from "../../api/regime";

const regimeBadge: Record<string, "success" | "warning" | "danger" | "info"> = {
  TREND: "success",
  DOWNTREND: "danger",
  RANGE: "warning",
  DEAD: "info",
};

export function MarketRegimeWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["regime"],
    queryFn: fetchRegime,
    refetchInterval: 30_000,
  });

  if (isLoading) return <Skeleton className="h-24 rounded-xl" />;

  if (!data || data.error) return null;

  return (
    <Card className="h-full">
      <CardContent className="p-4">
        <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em] mb-3">
          Market Regime
        </div>
        <div className="flex items-center gap-2 mb-3">
          <Badge variant={regimeBadge[data.regime] || "default"}>
            {data.regime}
          </Badge>
          <Badge
            variant={
              data.trend === "BULLISH"
                ? "success"
                : data.trend === "BEARISH"
                  ? "danger"
                  : "warning"
            }
          >
            {data.trend}
          </Badge>
        </div>
        <div className="grid grid-cols-3 gap-2 text-[11px] font-mono tabular-nums">
          <div>
            <div className="text-[var(--text-muted)] text-[10px]">Vol</div>
            <div className="text-[var(--text-primary)]">
              {(data.volatility * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[var(--text-muted)] text-[10px]">RSI</div>
            <div className="text-[var(--text-primary)]">{data.rsi}</div>
          </div>
          <div>
            <div className="text-[var(--text-muted)] text-[10px]">BTC</div>
            <div className="text-[var(--text-primary)]">
              {(data.btc_health * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
