import { useWidgetRegistry } from "./widget-registry";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { useWorkspaceStore } from "../../stores/workspace-store";

interface DashboardAnalyticsProps {
  compact?: boolean;
}

export function DashboardAnalytics({ compact = false }: DashboardAnalyticsProps) {
  const { getAllWidgets } = useWidgetRegistry();
  const { panels } = useWorkspaceStore();
  const allWidgets = getAllWidgets();
  const totalPanels = panels.length;

  const categoryCounts = allWidgets.reduce(
    (acc, w) => {
      acc[w.category] = (acc[w.category] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const categoryColors: Record<string, string> = {
    kpi: "var(--accent-blue)",
    portfolio: "var(--accent-green)",
    risk: "var(--accent-red)",
    monitoring: "var(--accent-yellow)",
    ai: "var(--accent-purple)",
    notification: "var(--accent-orange)",
    chart: "var(--accent-cyan)",
    market: "var(--accent-pink)",
  };

  if (compact) {
    return (
      <div className="flex items-center gap-3 text-[10px] font-mono text-[var(--text-muted)]">
        <span>{allWidgets.length} widgets</span>
        <span>{totalPanels} active</span>
      </div>
    );
  }

  const totalWidgets = allWidgets.length;
  const categories = Object.entries(categoryCounts).sort(([, a], [, b]) => b - a);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Dashboard Analytics</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {totalWidgets} widgets · {totalPanels} active panels
        </span>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {categories.map(([cat, count]) => {
            const pct = (count / totalWidgets) * 100;
            return (
              <div key={cat}>
                <div className="flex justify-between text-[10px] mb-0.5">
                  <span className="font-mono text-[var(--text-secondary)] uppercase tracking-wider">
                    {cat}
                  </span>
                  <span className="font-mono tabular-nums text-[var(--text-primary)]">
                    {count} ({pct.toFixed(0)}%)
                  </span>
                </div>
                <div className="h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: categoryColors[cat] || "var(--accent-blue)",
                    }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
