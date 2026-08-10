import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { fetchPortfolioWidgetSummary } from "../../api/widgets";
import { formatUSD } from "../../lib/utils";

export function PortfolioSummaryWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["portfolio-summary"],
    queryFn: fetchPortfolioWidgetSummary,
    refetchInterval: 10_000,
  });

  if (isLoading) return <Skeleton className="h-28 rounded-xl" />;

  const p = data;
  if (!p) return null;

  return (
    <Card className="h-full">
      <CardContent className="p-4">
        <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em] mb-3">
          Portfolio
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Total PnL</div>
            <div
              className={`text-sm font-mono tabular-nums font-medium ${
                p.total_pnl >= 0
                  ? "text-[var(--accent-green)]"
                  : "text-[var(--accent-red)]"
              }`}
            >
              {formatUSD(p.total_pnl)}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Win Rate</div>
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {p.win_rate.toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Open Trades</div>
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {p.open_trades}
            </div>
          </div>
          <div>
            <div className="text-[10px] text-[var(--text-muted)]">Max Drawdown</div>
            <div className="text-sm font-mono tabular-nums text-[var(--text-primary)]">
              {formatUSD(p.max_drawdown)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
