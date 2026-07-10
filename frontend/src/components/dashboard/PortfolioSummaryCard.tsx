import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { fetchPortfolioWidgetSummary } from "../../api/widgets";
import type { PortfolioSummaryDTO } from "../../types/api/widget";

export function PortfolioSummaryCard() {
  const [data, setData] = useState<PortfolioSummaryDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetchPortfolioWidgetSummary();
      setData(res.portfolio);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-24 w-full" />
        ) : !data ? (
          <p className="text-[10px] text-gray-600 font-mono">No portfolio data</p>
        ) : (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-widest">Total PnL</p>
              <p className={`text-sm font-mono ${data.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                ${data.total_pnl.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-widest">Win Rate</p>
              <p className="text-sm font-mono text-gray-100">{data.win_rate.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-widest">Open Trades</p>
              <p className="text-sm font-mono text-gray-100">{data.open_trades}</p>
            </div>
            <div>
              <p className="text-[10px] text-gray-600 uppercase tracking-widest">Avg PnL</p>
              <p className={`text-sm font-mono ${data.avg_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                ${data.avg_pnl.toFixed(2)}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
