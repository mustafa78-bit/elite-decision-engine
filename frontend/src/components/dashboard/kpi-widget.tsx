import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { fetchKpiDetail } from "../../api/widgets";
import { formatUSD } from "../../lib/utils";

const statusColors: Record<string, string> = {
  positive: "text-[var(--accent-green)]",
  negative: "text-[var(--accent-red)]",
  neutral: "text-[var(--text-secondary)]",
  good: "text-[var(--accent-green)]",
  warning: "text-[var(--accent-yellow)]",
};

const trends: Record<string, string> = {
  improving: "↑",
  declining: "↓",
  stable: "→",
};

const trendColors: Record<string, string> = {
  improving: "text-[var(--accent-green)]",
  declining: "text-[var(--accent-red)]",
  stable: "text-[var(--text-muted)]",
};

export function KPIWidget() {
  const { data, isLoading } = useQuery({
    queryKey: ["kpi-detail"],
    queryFn: fetchKpiDetail,
    refetchInterval: 10_000,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
    );
  }

  const kpis = data?.kpis || [];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {kpis.slice(0, 10).map((kpi, i) => (
        <motion.div
          key={kpi.name}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.04 }}
        >
          <Card className="hover:border-[var(--border-default)] transition-all">
            <CardContent className="p-3">
              <div className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em] mb-1.5">
                {kpi.name}
              </div>
              <div className="flex items-baseline gap-1.5">
                <span
                  className={`text-lg font-mono tabular-nums ${
                    statusColors[kpi.status] || "text-[var(--text-primary)]"
                  }`}
                >
                  {kpi.unit === "%"
                    ? `${kpi.value.toFixed(1)}%`
                    : kpi.unit === "USD"
                      ? kpi.value >= 1000
                        ? `$${(kpi.value / 1000).toFixed(1)}K`
                        : formatUSD(kpi.value)
                      : kpi.value.toLocaleString()}
                </span>
                <span
                  className={`text-xs ${trendColors[kpi.trend] || "text-[var(--text-muted)]"}`}
                >
                  {trends[kpi.trend] || ""}
                </span>
              </div>
              {kpi.change_pct !== undefined && kpi.change_pct !== 0 && (
                <div
                  className={`text-[10px] font-mono mt-0.5 ${
                    kpi.change_pct > 0
                      ? "text-[var(--accent-green)]"
                      : "text-[var(--accent-red)]"
                  }`}
                >
                  {kpi.change_pct > 0 ? "+" : ""}
                  {kpi.change_pct.toFixed(1)}%
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}
