import { useEffect, useState } from "react";
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

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    apiFetch<{ funding: FundingData[] }>("/funding")
      .then((res) => { if (mounted) setData(res.funding || []); })
      .catch(() => { if (mounted) setData([]); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);

  const rateBadge = (rate: number): "success" | "danger" | "warning" => {
    if (rate > 0.01) return "danger";
    if (rate > 0) return "warning";
    return "success";
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
          Funding Rates
        </h2>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-xs font-mono text-[var(--text-muted)]">No funding data available</p>
          </CardContent>
        </Card>
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
                  <div className="flex justify-between text-[var(--text-secondary)]">
                    <span>Predicted</span>
                    <span className={item.predicted_rate > 0 ? "text-[var(--accent-red)]" : "text-[var(--accent-green)]"}>
                      {(item.predicted_rate * 100).toFixed(3)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-[var(--text-secondary)]">
                    <span>Next Funding</span>
                    <span className="text-[var(--text-secondary)]">
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
