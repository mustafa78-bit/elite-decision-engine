import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchMonitoringWidgetStatus } from "../../api/widgets";

const statusVariant: Record<string, "success" | "danger" | "warning"> = {
  running: "success",
  healthy: "success",
  error: "danger",
  down: "danger",
  degraded: "warning",
};

export function MonitoringWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["monitoring"],
    queryFn: fetchMonitoringWidgetStatus,
    refetchInterval: 15_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
        {data && (
          <Badge
            variant={
              data.monitoring.status === "healthy" ? "success" : "warning"
            }
          >
            {data.monitoring.status}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : data?.monitoring.services ? (
          <div className="space-y-1.5">
            {Object.entries(data.monitoring.services).map(([name, status]) => (
              <motion.div
                key={name}
                className="flex items-center justify-between py-1"
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <span className="text-xs font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                  {name}
                </span>
                <Badge variant={statusVariant[status] || "default"}>
                  <span className="flex items-center gap-1">
                    {status === "running" && (
                      <span className="w-1 h-1 rounded-full bg-[var(--accent-green)] animate-pulse" />
                    )}
                    {status}
                  </span>
                </Badge>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No monitoring data
          </div>
        )}
      </CardContent>
    </Card>
  );
}
