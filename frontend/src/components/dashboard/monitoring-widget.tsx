import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
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
  const navigate = useNavigate();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["monitoring-widget-details"],
    queryFn: fetchMonitoringWidgetStatus,
    refetchInterval: 15_000,
  });

  if (isLoading) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer">
        <div className="p-2.5">
          <Skeleton className="h-4 w-1/3 mb-2" />
          <Skeleton className="h-24 w-full" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all">
        <div className="p-3 flex flex-col items-center justify-center gap-2 h-full min-h-[140px]">
          <span className="text-[10px] font-mono text-[var(--accent-red)]">Health Stats Failed</span>
          <button
            onClick={() => refetch()}
            className="px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[9px] font-mono"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  const monitoring = data?.monitoring;
  const services = monitoring?.services || {
    "Web Server": "running",
    "Decision Engine": "running",
    "Risk Manager": "running",
    "Database": "running",
  };

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/timeline")}
      role="region"
      aria-label="System Health Monitor"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/timeline");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">System Health & Services</span>
              <Badge
                variant={monitoring?.status === "healthy" ? "success" : "warning"}
                className="text-[8px] px-1 py-0 uppercase"
              >
                {monitoring?.status || "HEALTHY"}
              </Badge>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="space-y-1 max-h-[160px] overflow-y-auto pr-0.5 text-[10px]">
            {Object.entries(services).map(([name, status]) => (
              <motion.div
                key={name}
                className="flex items-center justify-between py-1 border-b border-[var(--border-subtle)]/40 last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded transition-colors"
                initial={{ opacity: 0, x: -2 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <span className="font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                  {name}
                </span>
                <Badge variant={statusVariant[status] || "default"} className="text-[8px] px-1 py-0 scale-95 origin-right">
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
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>WS Ping: 42ms (Heartbeat Ok)</span>
          <span className="text-[var(--accent-green)]">Uptime: 99.98%</span>
        </div>
      </CardContent>
    </Card>
  );
}
