import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { Badge } from "../components/ui/badge";
import { fetchPortfolioFull } from "../api/portfolio_detail";
import type { PortfolioFullDTO } from "../types/api/portfolio";

export default function PortfolioDetailPage() {
  const [data, setData] = useState<PortfolioFullDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchPortfolioFull();
      setData(res);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="border border-dashed border-gray-800 rounded p-8 text-center">
        <p className="text-xs text-gray-600 font-mono uppercase tracking-widest">
          No portfolio data
        </p>
      </div>
    );
  }

  const { summary, distribution, risk } = data;

  return (
    <div className="space-y-6">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Portfolio Detail
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Total PnL</CardTitle>
          </CardHeader>
          <CardContent>
            <span className={`text-lg font-mono ${summary.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ${summary.total_pnl.toFixed(2)}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Win Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-mono text-gray-100">
              {summary.win_rate.toFixed(1)}%
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Profit Factor</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-mono text-gray-100">
              {summary.profit_factor.toFixed(2)}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Sharpe</CardTitle>
          </CardHeader>
          <CardContent>
            <span className={`text-lg font-mono ${risk.sharpe >= 1 ? "text-green-400" : "text-yellow-400"}`}>
              {risk.sharpe.toFixed(2)}
            </span>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Max Drawdown</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-mono text-red-400">
              -${risk.max_drawdown.toFixed(2)}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Calmar</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-mono text-gray-100">
              {risk.calmar.toFixed(2)}
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recovery Factor</CardTitle>
          </CardHeader>
          <CardContent>
            <span className="text-lg font-mono text-gray-100">
              {risk.recovery_factor.toFixed(2)}
            </span>
          </CardContent>
        </Card>
      </div>

      {distribution.by_symbol && Object.keys(distribution.by_symbol).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Distribution by Symbol</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(distribution.by_symbol).map(([sym, val]) => (
                <Badge key={sym} variant="info">
                  {sym}: {typeof val === "number" ? val.toFixed(1) : String(val)}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
