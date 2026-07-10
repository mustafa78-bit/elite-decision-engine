import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { formatTime } from "../../lib/utils";

interface TimelineEvent {
  id: string;
  time: string;
  title: string;
  description: string;
  type: string;
}

interface TimelineWidgetProps {
  events?: TimelineEvent[];
}

const typeDot: Record<string, string> = {
  trade: "bg-[var(--accent-green)]",
  signal: "bg-[var(--accent-blue)]",
  risk: "bg-[var(--accent-yellow)]",
  error: "bg-[var(--accent-red)]",
  system: "bg-[var(--text-muted)]",
};

export function TimelineWidget({ events = [] }: TimelineWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Timeline</CardTitle>
      </CardHeader>
      <CardContent className="max-h-64 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No timeline events
          </div>
        ) : (
          <div className="relative pl-4 border-l border-[var(--border-subtle)] space-y-3">
            {events.slice(0, 8).map((evt) => (
              <div key={evt.id} className="relative">
                <span
                  className={`absolute -left-[17px] top-1 w-2 h-2 rounded-full ${typeDot[evt.type] || "bg-[var(--text-muted)]"} ring-2 ring-[var(--bg-base)]`}
                />
                <div className="text-[10px] font-mono text-[var(--text-muted)]">
                  {formatTime(evt.time)}
                </div>
                <div className="text-[11px] font-medium text-[var(--text-primary)] mt-0.5">
                  {evt.title}
                </div>
                <div className="text-[10px] text-[var(--text-secondary)] line-clamp-1">
                  {evt.description}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
