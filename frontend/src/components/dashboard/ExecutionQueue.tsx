import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchSignals } from "../../api/signals";

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  return `${hrs}h ${mins % 60}m ago`;
}

export default function ExecutionQueue() {
  const { data: signals, loading, error, refetch } = useApi(() => fetchSignals(20), []);

  const queue = (signals || []).filter((s) => s.status === "OPEN");

  return (
    <Card>
      <CardContent className="p-3">
        <div className="flex items-center justify-between mb-2">
          <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)]">Execution Queue</p>
          {!loading && <span className="text-[10px] font-mono text-[var(--text-muted)]">{queue.length} pending</span>}
        </div>

        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center gap-2 py-2">
            <p className="text-[10px] text-[var(--accent-red)] font-mono">Failed to load queue</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        ) : queue.length === 0 ? (
          <p className="text-[10px] text-[var(--text-muted)] font-mono text-center py-3">No pending signals in queue</p>
        ) : (
          <div className="space-y-1">
            {queue.slice(0, 5).map((s) => (
              <div key={s.id} className="flex items-center justify-between text-[10px] font-mono py-1 border-b border-[var(--border-subtle)] last:border-0">
                <div className="flex items-center gap-2">
                  <span className={s.side === "LONG" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                    {s.side === "LONG" ? "▲" : "▼"}
                  </span>
                  <span className="text-[var(--text-primary)]">{s.symbol}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[var(--text-muted)]">{(s.confidence * 100).toFixed(0)}%</span>
                  <span className="text-[var(--text-muted)] ">{timeAgo(s.created_at)}</span>
                </div>
              </div>
            ))}
            {queue.length > 5 && (
              <p className="text-[9px] text-[var(--text-muted)] text-center pt-1">+{queue.length - 5} more</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
