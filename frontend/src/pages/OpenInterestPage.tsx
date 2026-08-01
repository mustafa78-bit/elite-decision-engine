import { useEffect, useState } from "react";
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

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    apiFetch<{ open_interest: OIData[] }>("/open-interest")
      .then((res) => { if (mounted) setData(res.open_interest || []); })
      .catch(() => { if (mounted) setData([]); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  const formatUSD = (n: number) => {
    if (n >= 1_000_000_000) return `$${(n / 1_000_000_000).toFixed(2)}B`;
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(2)}M`;
    return `$${n.toLocaleString()}`;
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        Open Interest
      </h2>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-xs font-mono text-[var(--text-muted)]">No open interest data available</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {data.map((item) => (
            <Card key={item.symbol}>
              <CardHeader>
                <CardTitle>{item.symbol}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="text-lg font-mono text-[var(--text-primary)]">
                    {formatUSD(item.open_interest)}
                  </div>
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-[var(--text-secondary)]">24h Change</span>
                    <span className={item.change_24h >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                      {item.change_24h >= 0 ? "+" : ""}{item.change_24h}%
                    </span>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono">
                    <span className="text-[var(--text-secondary)]">Volume</span>
                    <span className="text-[var(--text-secondary)]">{formatUSD(item.volume)}</span>
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
