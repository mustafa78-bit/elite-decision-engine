import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { fetchMonitoringWidgetStatus } from "../../api/widgets";

const statusVariant: Record<string, "success" | "danger" | "warning"> = {
  running: "success",
  connected: "success",
  healthy: "success",
  error: "danger",
  down: "danger",
  disconnected: "danger",
  degraded: "warning",
  unknown: "warning",
};

export function MonitoringWidget() {
  const { t } = useTranslation("heroDashboard");
  const statusLabels: Record<string, string> = {
    running: t("monitoringWidget.status.running"),
    connected: t("monitoringWidget.status.connected"),
    healthy: t("monitoringWidget.status.healthy"),
    error: t("monitoringWidget.status.error"),
    down: t("monitoringWidget.status.down"),
    disconnected: t("monitoringWidget.status.disconnected"),
    degraded: t("monitoringWidget.status.degraded"),
    unknown: t("monitoringWidget.status.unknown"),
  };
  const nameLabels: Record<string, string> = {
    database: t("monitoringWidget.names.database"),
    collector: t("monitoringWidget.names.collector"),
  };
  const { data, isLoading } = useQuery({
    queryKey: ["monitoring"],
    queryFn: fetchMonitoringWidgetStatus,
    refetchInterval: 15_000,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("monitoringWidget.title")}</CardTitle>
        {data && (
          <Badge variant={data.status === "healthy" ? "success" : "warning"}>
            {data.status}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : data ? (
          <div className="space-y-1.5">
            {([
              ["database", data.database_status],
              ["collector", data.collector_status],
            ] as const).map(([name, status]) => (
              <motion.div
                key={name}
                className="flex items-center justify-between py-1"
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
              >
                <span className="text-xs font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                  {nameLabels[name] || name}
                </span>
                <Badge variant={statusVariant[status] || "default"}>
                  <span className="flex items-center gap-1">
                    {status === "connected" && (
                      <span className="w-1 h-1 rounded-full bg-[var(--accent-green)] animate-pulse" />
                    )}
                    {statusLabels[status] || status}
                  </span>
                </Badge>
              </motion.div>
            ))}
            <div className="flex items-center justify-between py-1">
              <span className="text-xs font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                {t("monitoringWidget.websocketClients")}
              </span>
              <span className="text-xs font-mono text-[var(--text-primary)]">
                {data.websocket_clients}
              </span>
            </div>
            {data.last_error && (
              <div className="text-[11px] text-[var(--accent-red)] font-mono pt-1">
                {data.last_error}
              </div>
            )}
          </div>
        ) : (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            {t("monitoringWidget.empty")}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
