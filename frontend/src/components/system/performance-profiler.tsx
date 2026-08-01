import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface Metric {
  label: string;
  value: string;
  change: string;
  direction: "up" | "down" | "stable";
  status: "good" | "warn" | "bad";
}

interface PerformanceProfilerProps {
  metrics?: Metric[];
}

export function PerformanceProfiler({
  metrics = [
    { label: "Order Latency", value: "12ms", change: "-8%", direction: "down", status: "good" },
    { label: "WebSocket Ping", value: "4ms", change: "0%", direction: "stable", status: "good" },
    { label: "API Response", value: "87ms", change: "+15%", direction: "up", status: "warn" },
    { label: "Render Time", value: "16ms", change: "-5%", direction: "down", status: "good" },
    { label: "Memory Usage", value: "342MB", change: "+12%", direction: "up", status: "warn" },
    { label: "CPU Load", value: "23%", change: "+3%", direction: "up", status: "good" },
  ],
}: PerformanceProfilerProps) {
  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Performance Profiler</CardTitle></CardHeader>
      <CardContent className="grid grid-cols-2 gap-1.5">
        {metrics.map((m, i) => (
          <div key={i} className="p-2 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
            <div className="text-[8px] font-mono text-[var(--text-muted)] uppercase mb-0.5">{m.label}</div>
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-mono font-bold tabular-nums">{m.value}</span>
              <div className="flex items-center gap-1">
                <span className={`text-[9px] font-mono tabular-nums ${m.direction === "up" ? "text-[var(--accent-red)]" : m.direction === "down" ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]"}`}>
                  {m.change}
                </span>
                <Badge variant={m.status === "good" ? "success" : m.status === "warn" ? "warning" : "danger"} className="text-[7px] w-6 text-center">{m.status === "good" ? "OK" : m.status === "warn" ? "!" : "!!"}</Badge>
              </div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
