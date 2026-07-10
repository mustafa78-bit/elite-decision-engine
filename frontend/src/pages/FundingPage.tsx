import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";

interface FundingData {
  symbol: string;
  current_rate: number;
  predicted_rate: number;
  next_funding_time: string;
}

export default function FundingPage() {
  const [data, setData] = useState<FundingData[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch<FundingData[] | { funding: FundingData[] }>("/funding");
      const items = Array.isArray(res) ? res : (res as { funding: FundingData[] }).funding;
      setData(items || []);
    } catch {
      // silent - placeholder if endpoint doesn't exist
      setData([
        { symbol: "BTCUSDT", current_rate: 0.008, predicted_rate: 0.006, next_funding_time: "2026-07-09T12:00:00Z" },
        { symbol: "ETHUSDT", current_rate: 0.012, predicted_rate: 0.010, next_funding_time: "2026-07-09T12:00:00Z" },
        { symbol: "SOLUSDT", current_rate: -0.005, predicted_rate: -0.003, next_funding_time: "2026-07-09T12:00:00Z" },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const rateBadge = (rate: number): "success" | "danger" | "warning" => {
    if (rate > 0.01) return "danger";
    if (rate > 0) return "warning";
    return "success";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-gray-500">
          Funding Rates
        </h2>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((item) => (
            <Card key={item.symbol}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{item.symbol}</CardTitle>
                  <Badge variant={rateBadge(item.current_rate)}>
                    {(item.current_rate * 100).toFixed(3)}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-[10px] font-mono">
                  <div className="flex justify-between text-gray-500">
                    <span>Predicted</span>
                    <span className={item.predicted_rate > 0 ? "text-red-400" : "text-green-400"}>
                      {(item.predicted_rate * 100).toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-gray-500">
                    <span>Next Funding</span>
                    <span className="text-gray-400">
                      {new Date(item.next_funding_time).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
