import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface PerformanceWidgetProps {
  sharpeRatio?: number;
  sortinoRatio?: number;
  maxDrawdown?: number;
  winRate?: number;
  totalTrades?: number;
  profitFactor?: number;
}

export function PerformanceWidget({
  sharpeRatio = 0,
  sortinoRatio = 0,
  maxDrawdown = 0,
  winRate = 0,
  totalTrades = 0,
  profitFactor = 0,
}: PerformanceWidgetProps) {
  const { t } = useTranslation("heroDashboard");
  const metrics = [
    {
      label: t("performanceWidget.metrics.sharpe"),
      value: sharpeRatio.toFixed(2),
      color:
        sharpeRatio >= 1.5
          ? "text-[var(--accent-green)]"
          : sharpeRatio >= 0.5
            ? "text-[var(--accent-yellow)]"
            : "text-[var(--accent-red)]",
    },
    {
      label: t("performanceWidget.metrics.sortino"),
      value: sortinoRatio.toFixed(2),
      color:
        sortinoRatio >= 2
          ? "text-[var(--accent-green)]"
          : sortinoRatio >= 1
            ? "text-[var(--accent-yellow)]"
            : "text-[var(--accent-red)]",
    },
    {
      label: t("performanceWidget.metrics.winRate"),
      value: `${winRate.toFixed(1)}%`,
      color:
        winRate >= 60
          ? "text-[var(--accent-green)]"
          : winRate >= 40
            ? "text-[var(--accent-yellow)]"
            : "text-[var(--accent-red)]",
    },
    {
      label: t("performanceWidget.metrics.profitFactor"),
      value: profitFactor.toFixed(2),
      color:
        profitFactor >= 2
          ? "text-[var(--accent-green)]"
          : profitFactor >= 1
            ? "text-[var(--accent-yellow)]"
            : "text-[var(--accent-red)]",
    },
    {
      label: t("performanceWidget.metrics.maxDd"),
      value: `${Math.abs(maxDrawdown).toFixed(1)}%`,
      color:
        Math.abs(maxDrawdown) < 15
          ? "text-[var(--accent-green)]"
          : Math.abs(maxDrawdown) < 30
            ? "text-[var(--accent-yellow)]"
            : "text-[var(--accent-red)]",
    },
    {
      label: t("performanceWidget.metrics.trades"),
      value: totalTrades.toLocaleString(),
      color: "text-[var(--text-primary)]",
    },
  ];

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{t("performanceWidget.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2">
          {metrics.map((m) => (
            <div
              key={m.label}
              className="p-2 rounded-lg bg-[var(--bg-elevated)]/50"
            >
              <div className="text-[9px] text-[var(--text-muted)] uppercase tracking-wider">
                {m.label}
              </div>
              <div className={`text-xs font-mono font-medium tabular-nums ${m.color}`}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
