import { Card, CardContent } from "../ui/card";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchExecutionStatus } from "../../api/execution";
import { fetchNotifications } from "../../api/notifications";
import { useNavigate } from "react-router-dom";

export default function ActionCenter() {
  const nav = useNavigate();
  const { data: exec, loading: execLoading } = useApi(() => fetchExecutionStatus(), []);
  const { data: notifsData, loading: notifLoading } = useApi(() => fetchNotifications(1), []);

  const loading = execLoading || notifLoading;

  const items = [
    {
      label: "Pending Signals",
      value: exec?.signals.pending ?? "—",
      color: "var(--accent-yellow)",
      path: "/signals-ranking",
    },
    {
      label: "Open Trades",
      value: exec?.trades.open ?? "—",
      color: "var(--accent-green)",
      path: "/paper-trading",
    },
    {
      label: "Execution Rate",
      value: exec ? `${(exec.signals.execution_rate * 100).toFixed(0)}%` : "—",
      color: "var(--accent-blue)",
      path: "/execution",
    },
    {
      label: "Unread",
      value: notifsData?.total ?? "—",
      color: "var(--accent-red)",
      path: "/notifications",
    },
  ];

  return (
    <Card>
      <CardContent className="p-3">
        <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] mb-2">Action Center</p>

        {loading ? (
          <div className="grid grid-cols-2 gap-2">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-2">
            {items.map((item) => (
              <button
                key={item.label}
                onClick={() => nav(item.path)}
                className="flex flex-col items-center justify-center gap-0.5 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-base)] py-2 px-1 hover:bg-[var(--bg-elevated)] hover:border-[var(--border-default)] transition-colors cursor-pointer"
              >
                <span className="text-lg font-mono font-bold" style={{ color: item.color }}>
                  {item.value}
                </span>
                <span className="text-[9px] font-mono text-[var(--text-muted)] leading-tight text-center">
                  {item.label}
                </span>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
