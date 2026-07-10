import { useCallback, useEffect, useState } from "react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Skeleton } from "../components/ui/skeleton";
import { fetchGlobalTimeline } from "../api/timeline";
import type { TimelineEventDTO } from "../types/api/timeline";

const typeBadge: Record<string, string> = {
  trade: "success",
  signal: "info",
  risk: "warning",
  system: "default",
};

export default function TimelinePage() {
  const [events, setEvents] = useState<TimelineEventDTO[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchGlobalTimeline({ limit: 50 });
      setEvents(res.events);
      setTotal(res.total);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs uppercase tracking-widest text-gray-500">
          Timeline
        </h2>
        <span className="text-[10px] text-gray-600 font-mono">
          {total} events
        </span>
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 10 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : events.length === 0 ? (
        <div className="border border-dashed border-gray-800 rounded p-8 text-center">
          <p className="text-xs text-gray-600 font-mono uppercase tracking-widest">
            No timeline events
          </p>
        </div>
      ) : (
        <div className="space-y-1">
          {events.map((e) => (
            <Card key={e.id} className="p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Badge variant={(typeBadge[e.type] as "success" | "info" | "warning" | "default") || "default"}>
                    {e.type}
                  </Badge>
                  <span className="text-xs text-gray-300 font-mono">
                    {e.data?.symbol as string || e.data?.event_type as string || `#${e.id}`}
                  </span>
                </div>
                <span className="text-[10px] text-gray-600 font-mono">
                  {e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : ""}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
