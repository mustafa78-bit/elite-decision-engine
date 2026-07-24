import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";
import { apiFetch } from "../../api/client";

interface ServiceStatus {
  label: string;
  status: "ONLINE" | "OFFLINE" | "DEGRADED";
  detail?: string;
}

const statusVariant: Record<string, "success" | "danger" | "warning"> = {
  ONLINE: "success",
  OFFLINE: "danger",
  DEGRADED: "warning",
};

const statusDot: Record<string, string> = {
  ONLINE: "var(--accent-green)",
  OFFLINE: "var(--accent-red)",
  DEGRADED: "var(--accent-yellow)",
};

export function FounderHealthWidget() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);

    Promise.all([
      apiFetch<{ status: string }>("/health").catch(() => null),
      apiFetch<{
        database?: { status: string };
        collector?: { status: string };
        execution?: { status: string };
        dependencies?: Record<string, { status: string }>;
        metrics?: { status: string };
      }>("/health/details").catch(() => null),
      apiFetch<{ total?: number }>("/notifications/stats").catch(() => null),
    ]).then(([health, details, _notifStats]) => {
      if (!mounted) return;

      const items: ServiceStatus[] = [];

      const backendOk = health?.status === "ok";
      items.push({
        label: "Backend",
        status: backendOk ? "ONLINE" : "OFFLINE",
      });

      const db = details?.database;
      items.push({
        label: "Database",
        status: db?.status === "ok" ? "ONLINE" : db?.status === "error" ? "OFFLINE" : "DEGRADED",
        detail: db?.status !== "ok" ? (db as { detail?: string })?.detail : undefined,
      });

      items.push({
        label: "WebSocket",
        status: backendOk ? "ONLINE" : "OFFLINE",
      });

      const collector = details?.collector;
      const marketStatus = collector?.status === "ok" ? "ONLINE" : collector?.status === "error" ? "OFFLINE" : "DEGRADED";
      items.push({
        label: "Market Feed",
        status: marketStatus,
        detail: marketStatus !== "ONLINE" ? (collector as { detail?: string })?.detail ?? undefined : undefined,
      });

      const exec = details?.execution;
      const intelOk = exec?.status === "ok";
      items.push({
        label: "Intelligence Engine",
        status: intelOk ? "ONLINE" : "DEGRADED",
      });

      const deps = details?.dependencies || {};
      const notifOk = Object.values(deps).some((d) => d.status === "ok");
      items.push({
        label: "Notifications",
        status: notifOk ? "ONLINE" : "DEGRADED",
      });

      setServices(items);
      setLoading(false);
    }).catch(() => {
      if (!mounted) return;
      setServices([
        { label: "Backend", status: "OFFLINE" },
        { label: "Database", status: "OFFLINE" },
        { label: "WebSocket", status: "OFFLINE" },
        { label: "Market Feed", status: "OFFLINE" },
        { label: "Intelligence Engine", status: "OFFLINE" },
        { label: "Notifications", status: "OFFLINE" },
      ]);
      setLoading(false);
    });

    return () => { mounted = false; };
  }, []);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>System Health</CardTitle>
        <Badge
          variant={
            services.every((s) => s.status === "ONLINE")
              ? "success"
              : services.some((s) => s.status === "OFFLINE")
                ? "danger"
                : "warning"
          }
        >
          {loading
            ? "CHECKING"
            : services.every((s) => s.status === "ONLINE")
              ? "ALL ONLINE"
              : services.some((s) => s.status === "OFFLINE")
                ? "SOME OFFLINE"
                : "DEGRADED"}
        </Badge>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full rounded" />
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            {services.map((s) => (
              <div
                key={s.label}
                className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0"
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: statusDot[s.status] }}
                  />
                  <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                    {s.label}
                  </span>
                </div>
                <Badge variant={statusVariant[s.status]}>{s.status}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
