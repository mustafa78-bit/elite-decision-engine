import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface DecisionEvent {
  id: string;
  time: string;
  type: "signal" | "analysis" | "alert" | "execution";
  symbol: string;
  action: string;
  confidence: number;
  outcome?: "pending" | "correct" | "incorrect";
}

interface DecisionTimelineProps {
  events?: DecisionEvent[];
}

const typeConfig = {
  signal: { badge: "info" as const, icon: "⚡" },
  analysis: { badge: "purple" as const, icon: "✦" },
  alert: { badge: "warning" as const, icon: "⚠" },
  execution: { badge: "success" as const, icon: "▶" },
};

const outcomeConfig = {
  pending: { label: "Pending", badge: "default" as const },
  correct: { label: "Correct", badge: "success" as const },
  incorrect: { label: "Incorrect", badge: "danger" as const },
};

export function DecisionTimeline({ events = [] }: DecisionTimelineProps) {
  if (events.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>Decision Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No recent decisions
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Decision Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {events.map((e, i) => {
            const config = typeConfig[e.type];
            const outcome = outcomeConfig[e.outcome || "pending"];
            return (
              <div key={e.id} className="relative pl-4 pb-2 last:pb-0">
                {i < events.length - 1 && (
                  <div className="absolute left-[5px] top-3 bottom-0 w-px bg-[var(--border-subtle)]" />
                )}
                <div className="absolute left-[2px] top-[4px] w-[8px] h-[8px] rounded-full border-2 border-[var(--accent-blue)] bg-[var(--bg-base)]" />
                <div className="flex items-center justify-between mb-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[12px]">{config.icon}</span>
                    <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                      {e.symbol} · {e.action}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <span className="text-[11px] font-mono text-[var(--text-muted)]">
                      {e.time}
                    </span>
                    <Badge variant={outcome.badge}>{outcome.label}</Badge>
                  </div>
                </div>
                <div className="flex gap-2 text-[12px] font-mono text-[var(--text-muted)]">
                  <span>Confidence: {e.confidence}%</span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
