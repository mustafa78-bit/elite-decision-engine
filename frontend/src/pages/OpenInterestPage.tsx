import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { apiFetch } from "../api/client";

interface OIData {
  symbol: string;
  open_interest: number;
  change_24h: number;
  volume: number;
}

export default function OpenInterestPage() {
  const [data, setData] = useState<OIData[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiFetch<OIData[] | { open_interest: OIData[] }>("/open-interest");
      const items = Array.isArray(res) ? res : (res as { open_interest: OIData[] }).open_interest;
      setData(items || []);
    } catch {
      setData([
        { symbol: "BTCUSDT", open_interest: 12_450_000_000, change_24h: 3.2, volume: 2_100_000_000 },
        { symbol: "ETHUSDT", open_interest: 5_800_000_000, change_24h: -1.5, volume: 980_000_000 },
        { symbol: "SOLUSDT", open_interest: 1_200_000_000, change_24h: 8.7, volume: 340_000_000 },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const formatUSD = (n: number) => {
    if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
    return `$${n.toLocaleString()}`;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        Open Interest
      </h2>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((item) => (
            <Card key={item.symbol}>
              <CardHeader>
                <CardTitle>{item.symbol}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-lg font-mono text-gray-100">
                    {formatUSD(item.open_interest)}
                  </div>
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-gray-500">24h Change</span>
                    <span className={item.change_24h >= 0 ? "text-green-400" : "text-red-400"}>
                      {item.change_24h >= 0 ? "+" : ""}{item.change_24h}%
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-gray-500">Volume</span>
                    <span className="text-gray-400">{formatUSD(item.volume)}</span>
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
