import type { KPIDTO } from "../../types/api/widget";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

const statusColors: Record<string, string> = {
  positive: "text-green-400",
  negative: "text-red-400",
  neutral: "text-gray-400",
  good: "text-green-400",
  warning: "text-yellow-400",
};

const trendIcons: Record<string, string> = {
  improving: "↑",
  declining: "↓",
  stable: "→",
};

interface KPICardProps {
  kpi: KPIDTO;
}

export function KPICard({ kpi }: KPICardProps) {
  const valueColor = statusColors[kpi.status] || "text-gray-100";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{kpi.name}</CardTitle>
          {kpi.change_pct !== undefined && kpi.change_pct !== 0 && (
            <span className={`text-[10px] ${kpi.change_pct > 0 ? "text-green-500" : "text-red-500"}`}>
              {kpi.change_pct > 0 ? "+" : ""}{kpi.change_pct.toFixed(1)}%
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <span className={`text-lg font-mono ${valueColor}`}>
            {typeof kpi.value === "number" ? kpi.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : kpi.value}
          </span>
          <span className="text-[10px] text-gray-600 font-mono">{kpi.unit}</span>
          <span className={`text-xs ml-auto ${trendIcons[kpi.trend] === "↑" ? "text-green-500" : trendIcons[kpi.trend] === "↓" ? "text-red-500" : "text-gray-600"}`}>
            {trendIcons[kpi.trend] || ""}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

interface KpiGridProps {
  kpis: KPIDTO[];
  title?: string;
}

export function KpiGrid({ kpis, title }: KpiGridProps) {
  if (kpis.length === 0) return null;

  return (
    <section>
      {title && (
        <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-3">
          {title}
        </h2>
      )}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {kpis.map((kpi) => (
          <KPICard key={kpi.name} kpi={kpi} />
        ))}
      </div>
    </section>
  );
}
