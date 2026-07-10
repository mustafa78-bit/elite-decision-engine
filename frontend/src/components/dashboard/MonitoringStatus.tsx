import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchMonitoringWidgetStatus } from "../../api/widgets";
import type { MonitoringStatusDTO } from "../../types/api/widget";

export function MonitoringStatus() {
  const [data, setData] = useState<MonitoringStatusDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const res = await fetchMonitoringWidgetStatus();
      setData(res.monitoring);
    } catch {
      // silent
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
        ) : !data ? (
          <p className="text-[10px] text-gray-600 font-mono">No status data</p>
        ) : (
          <div className="space-y-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={data.status === "healthy" ? "success" : "warning"}>
                {data.status}
              </Badge>
            </div>
            {data.services && Object.entries(data.services).map(([name, s]) => (
              <div key={name} className="flex items-center justify-between py-0.5">
                <span className="text-[10px] font-mono text-gray-400 uppercase">{name}</span>
                <Badge variant={serviceBadge(s)}>{s}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
