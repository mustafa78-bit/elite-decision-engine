import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";
import { Skeleton } from "../ui/skeleton";

interface EcoEvent {
  id: string;
  time: string;
  currency: string;
  name: string;
  impact: "HIGH" | "MEDIUM" | "LOW";
  actual: string;
  forecast: string;
  previous: string;
}

const mockEvents: EcoEvent[] = [
  { id: "1", time: "14:30", currency: "USD", name: "Core CPI (MoM) (Jan)", impact: "HIGH", actual: "0.3%", forecast: "0.2%", previous: "0.3%" },
  { id: "2", time: "14:30", currency: "USD", name: "Initial Jobless Claims", impact: "MEDIUM", actual: "218K", forecast: "220K", previous: "224K" },
  { id: "3", time: "18:00", currency: "EUR", name: "ECB President Lagarde Speech", impact: "HIGH", actual: "--", forecast: "--", previous: "--" },
  { id: "4", time: "Tomorrow", currency: "USD", name: "Non-Farm Payrolls (NFP)", impact: "HIGH", actual: "--", forecast: "180K", previous: "216K" },
  { id: "5", time: "Tomorrow", currency: "USD", name: "Unemployment Rate", impact: "HIGH", actual: "--", forecast: "3.8%", previous: "3.7%" },
];

export function EconomicCalendarWidget() {
  const navigate = useNavigate();

  const { data: events, isLoading, error, refetch } = useQuery<EcoEvent[]>({
    queryKey: ["economic-calendar-events"],
    queryFn: async () => {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return mockEvents;
    },
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer">
        <div className="p-2.5">
          <Skeleton className="h-4 w-1/3 mb-2" />
          <Skeleton className="h-24 w-full" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all">
        <div className="p-3 flex flex-col items-center justify-center gap-2 h-full min-h-[140px]">
          <span className="text-[10px] font-mono text-[var(--accent-red)]">Economic Calendar Failed</span>
          <button
            onClick={() => refetch()}
            className="px-2 py-0.5 rounded bg-[var(--bg-elevated)] border border-[var(--border-default)] hover:bg-[var(--bg-hover)] text-[9px] font-mono"
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all cursor-pointer"
      onClick={() => navigate("/timeline")}
      role="region"
      aria-label="Economic Calendar"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          navigate("/timeline");
        }
      }}
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Economic Calendar</span>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Link</span>
          </div>

          <div className="space-y-1 max-h-[160px] overflow-y-auto pr-0.5">
            {events && events.length > 0 ? (
              events.map((e) => (
                <div key={e.id} className="py-1 border-b border-[var(--border-subtle)] last:border-0 hover:bg-[var(--bg-hover)] px-1 rounded transition-colors text-[10px]">
                  <div className="flex items-start justify-between gap-1 mb-0.5">
                    <div className="flex items-center gap-1">
                      <span className="text-[9px] text-[var(--text-muted)] font-mono font-semibold">{e.time}</span>
                      <span className="text-[8px] bg-[var(--bg-elevated)] text-[var(--text-secondary)] px-0.5 rounded font-mono">{e.currency}</span>
                      <span className="font-medium text-[var(--text-primary)] leading-tight">{e.name}</span>
                    </div>
                    <Badge variant={e.impact === "HIGH" ? "danger" : e.impact === "MEDIUM" ? "warning" : "info"} className="text-[7px] px-0.5 py-0 uppercase shrink-0 scale-95 origin-right">
                      {e.impact}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between font-mono text-[9px] text-[var(--text-muted)] pl-7">
                    <span>Act: <span className="text-[var(--text-secondary)]">{e.actual}</span></span>
                    <span>Cons: <span className="text-[var(--text-secondary)]">{e.forecast}</span></span>
                    <span>Prev: <span className="text-[var(--text-secondary)]">{e.previous}</span></span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-[10px] text-[var(--text-muted)] font-mono">
                No economic events scheduled
              </div>
            )}
          </div>
        </div>

        <div className="mt-2 pt-1.5 border-t border-[var(--border-subtle)] text-[9px] font-mono text-[var(--text-muted)] flex items-center justify-between">
          <span>Source: Bloomberg Economic Feed</span>
          <span className="text-[var(--accent-cyan)] font-semibold">FOMC in 12 Days</span>
        </div>
      </CardContent>
    </Card>
  );
}
