import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { fetchMonitoringWidgetStatus } from "../../api/widgets";
import type { MonitoringStatusDTO } from "../../types/api/widget";

export function MonitoringStatus() {
  const [data, setData] = useState<MonitoringStatusDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchMonitoringWidgetStatus();
      setData(res.monitoring);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load monitoring status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const serviceBadge = (status: string): "success" | "danger" | "warning" => {
    if (status === "running" || status === "healthy") return "success";
    if (status === "error" || status === "down") return "danger";
    return "warning";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Status</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-20 w-full" />
        ) : error ? (
          <div className="flex flex-col items-center gap-3 py-3">
            <p className="text-[11px] text-[var(--accent-red)] font-mono text-center">{error}</p>
            <Button variant="ghost" size="sm" onClick={load}>Retry</Button>
          </div>
        ) : !data ? (
          <p className="text-[10px] text-[var(--text-muted)] font-mono">No status data</p>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={data.status === "healthy" ? "success" : "warning"}>
                {data.status}
              </Badge>
            </div>
            {data.services && Object.entries(data.services).map(([name, s]) => (
              <div key={name} className="flex items-center justify-between py-0.5">
                <span className="text-[10px] font-mono text-[var(--text-secondary)] uppercase">{name}</span>
                <Badge variant={serviceBadge(s)}>{s}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
