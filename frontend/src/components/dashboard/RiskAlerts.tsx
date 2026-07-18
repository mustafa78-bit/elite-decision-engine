import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchRisk, type RiskData } from "../../api/risk";

interface Alert {
  severity: "high" | "warning";
  label: string;
  detail: string;
}

function computeAlerts(r: RiskData): Alert[] {
  const alerts: Alert[] = [];

  if (r.risk_score > 0.7) {
    alerts.push({ severity: "high", label: "Risk Score", detail: `${(r.risk_score * 100).toFixed(0)}%` });
  } else if (r.risk_score > 0.5) {
    alerts.push({ severity: "warning", label: "Risk Score", detail: `${(r.risk_score * 100).toFixed(0)}%` });
  }

  const openPct = r.max_open_trades > 0 ? r.open_trades / r.max_open_trades : 0;
  if (openPct >= 1) {
    alerts.push({ severity: "high", label: "Open Trades", detail: `${r.open_trades}/${r.max_open_trades}` });
  } else if (openPct >= 0.8) {
    alerts.push({ severity: "warning", label: "Open Trades", detail: `${r.open_trades}/${r.max_open_trades}` });
  }

  for (const [sym, exposure] of Object.entries(r.symbol_exposure)) {
    if (r.max_symbol_exposure <= 0) continue;
    const expPct = exposure / r.max_symbol_exposure;
    if (expPct >= 1) {
      alerts.push({ severity: "high", label: sym, detail: `Exposure limit` });
    } else if (expPct >= 0.8) {
      alerts.push({ severity: "warning", label: sym, detail: `Exposure ${(expPct * 100).toFixed(0)}%` });
    }
  }

  const pfPct = r.max_portfolio_exposure > 0 ? r.portfolio_exposure / r.max_portfolio_exposure : 0;
  if (pfPct >= 1) {
    alerts.push({ severity: "high", label: "Portfolio Exposure", detail: `${(r.portfolio_exposure / 1000).toFixed(1)}K` });
  } else if (pfPct >= 0.8) {
    alerts.push({ severity: "warning", label: "Portfolio Exposure", detail: `${(pfPct * 100).toFixed(0)}%` });
  }

  const dlPct = r.max_daily_loss > 0 ? Math.abs(r.daily_loss) / r.max_daily_loss : 0;
  if (dlPct >= 0.8) {
    alerts.push({ severity: "high", label: "Daily Loss", detail: `${Math.abs(r.daily_loss).toFixed(0)}` });
  } else if (dlPct >= 0.5) {
    alerts.push({ severity: "warning", label: "Daily Loss", detail: `${Math.abs(r.daily_loss).toFixed(0)}` });
  }

  return alerts.sort((a, _b) => (a.severity === "high" ? -1 : 1));
}

export default function RiskAlerts() {
  const { data: risk, loading, error, refetch } = useApi(() => fetchRisk(), []);

  const alerts = risk ? computeAlerts(risk) : [];

  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)]">Risk Alerts</p>
          {!loading && !error && (
            <span className="text-[10px] font-mono text-[var(--text-muted)]">
              {alerts.length > 0 ? `${alerts.filter(a => a.severity === "high").length} critical` : "All clear"}
            </span>
          )}
        </div>

        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <p className="text-[10px] text-[var(--accent-red)] font-mono">Failed to load</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        ) : alerts.length === 0 ? (
          <p className="text-[10px] text-[var(--text-muted)] font-mono text-center py-3">No active alerts</p>
        ) : (
          <div className="space-y-1">
            {alerts.slice(0, 4).map((a) => (
              <div key={a.label} className="flex items-center justify-between text-[10px] font-mono py-1 border-b border-[var(--border-subtle)] last:border-0">
                <div className="flex items-center gap-2">
                  <span className={a.severity === "high" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"}>
                    {a.severity === "high" ? "●" : "○"}
                  </span>
                  <span className="text-[var(--text-primary)]">{a.label}</span>
                </div>
                <span className="text-[var(--text-muted)]">{a.detail}</span>
              </div>
            ))}
            {alerts.length > 4 && (
              <p className="text-[9px] text-[var(--text-muted)] text-center pt-1">+{alerts.length - 4} more</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
