import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchRegime } from "../../api/regime";
import type { RegimeData } from "../../api/regime";

const regimeColors: Record<string, string> = {
  TREND: "bg-green-900/40 text-green-400 border-green-800",
  DOWNTREND: "bg-red-900/40 text-red-400 border-red-800",
  RANGE: "bg-yellow-900/40 text-yellow-400 border-yellow-800",
  DEAD: "bg-gray-900 text-gray-500 border-gray-800",
};

export function MarketRegimeWidget() {
  const [data, setData] = useState<RegimeData | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const d = await fetchRegime();
      if (!d.error) setData(d);
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
        <CardTitle>Market Regime</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-20 w-full" />
        ) : !data ? (
          <p className="text-[10px] text-gray-600 font-mono">No regime data</p>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className={`px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider rounded border ${regimeColors[data.regime] || regimeColors.RANGE}`}>
                {data.regime}
              </span>
              <Badge variant={data.trend === "BULLISH" ? "success" : data.trend === "BEARISH" ? "danger" : "warning"}>
                {data.trend}
              </Badge>
            </div>
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
              <div>
                <span className="text-gray-600">Vol </span>
                <span className="text-gray-300">{(data.volatility * 100).toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-gray-600">RSI </span>
                <span className="text-gray-300">{data.rsi}</span>
              </div>
              <div>
                <span className="text-gray-600">BTC </span>
                <span className="text-gray-300">{(data.btc_health * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
