import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

interface RiskMetric {
  label: string;
  value: string;
  status: "good" | "warning" | "danger";
}

const defaultMetrics: RiskMetric[] = [
  { label: "Portfolio Risk Score", value: "3.2 / 10.0", status: "good" },
  { label: "Value at Risk (VaR 95%)", value: "$1,450.00", status: "good" },
  { label: "Value at Risk (VaR 99%)", value: "$2,890.00", status: "warning" },
  { label: "Active Drawdown", value: "-1.15%", status: "good" },
  { label: "Max Historical Drawdown", value: "-6.40%", status: "good" },
];

interface RiskWidgetProps {
  riskMetrics?: RiskMetric[];
  overallRisk?: "LOW" | "MEDIUM" | "HIGH";
}

const statusColor: Record<string, string> = {
  good: "var(--accent-green)",
  warning: "var(--accent-yellow)",
  danger: "var(--accent-red)",
};

export function RiskWidget({
  riskMetrics = defaultMetrics,
  overallRisk = "LOW",
}: RiskWidgetProps) {
  const navigate = useNavigate();

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/risk")}
      role="region"
      aria-label="Risk Command Center"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/risk");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Risk Command Center</span>
              <Badge
                variant={
                  overallRisk === "LOW"
                    ? "success"
                    : overallRisk === "MEDIUM"
                      ? "warning"
                      : "danger"
                }
                className="text-[8px] px-1 py-0 uppercase"
              >
                {overallRisk} RISK
              </Badge>
            </div>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-0.5 text-[10px]">
            {riskMetrics.map((m) => (
              <div key={m.label} className="py-0.5 border-b border-[var(--border-subtle)]/40 last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded transition-colors">
                <div className="flex justify-between text-[10px] mb-0.5">
                  <span className="text-[var(--text-secondary)] font-mono">
                    {m.label}
                  </span>
                  <span className="font-mono font-bold text-[var(--text-primary)]">
                    {m.value}
                  </span>
                </div>
                <div className="h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: m.status === "good" ? "32%" : m.status === "warning" ? "65%" : "85%",
                      background: statusColor[m.status] || "var(--accent-yellow)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Exposure Warn: Normal (0 Active)</span>
          <span className="text-[var(--accent-green)] font-semibold">Stress Test: Safe</span>
        </div>
      </CardContent>
    </Card>
  );
}
