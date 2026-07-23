import { Card, CardContent } from "../ui/card";
import { Button } from "../ui/button";
import { Skeleton } from "../ui/skeleton";
import { useApi } from "../../hooks/useApi";
import { fetchWhaleActivity } from "../../api/whale";

export default function WhaleActivityCard() {
  const { data: activities, loading, error, refetch } = useApi(() => fetchWhaleActivity(), []);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[9px] font-semibold tracking-[0.1em] uppercase" style={{ color: "var(--text-muted)" }}>
            Whale Intelligence
          </span>
          {!loading && !error && (
            <span className="text-[8px] font-mono" style={{ color: "var(--text-disabled)" }}>
              {activities && activities.length > 0 ? `${activities.length} signal${activities.length > 1 ? "s" : ""}` : "None"}
            </span>
          )}
        </div>

        {loading ? (
          <div className="space-y-2">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-3/4" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-between gap-3 py-1">
            <p className="text-[10px] font-mono" style={{ color: "var(--accent-red)" }}>Failed to load</p>
            <Button variant="ghost" size="sm" onClick={refetch}>Retry</Button>
          </div>
        ) : !activities || activities.length === 0 ? (
          <p className="text-[11px] font-mono text-center py-4" style={{ color: "var(--text-disabled)" }}>
            No whale activity detected
          </p>
        ) : (
          <div className="space-y-1.5">
            {activities.slice(0, 3).map((a, i) => (
              <div
                key={`${a.symbol}-${i}`}
                className="flex items-center justify-between py-1.5 border-b text-[10px] font-mono"
                style={{
                  borderColor: "#243244",
                  animation: `fadeSlideUp 0.3s ease-out ${i * 0.06}s both`,
                }}
              >
                <div className="flex items-center gap-2">
                  <span
                    className="w-[5px] h-[5px] rounded-full"
                    style={{
                      background: a.severity === "high" ? "#EF4444" : "#06B6D4",
                      animation: a.severity === "high" ? "glow 2s ease-in-out infinite" : "none",
                    }}
                  />
                  <span style={{ color: "var(--text-primary)" }}>{a.symbol}</span>
                  <span
                    className="text-[8px] px-1.5 py-0.5 rounded-md"
                    style={{
                      background: a.severity === "high" ? "rgba(239,68,68,0.1)" : "rgba(6,182,212,0.1)",
                      color: a.severity === "high" ? "#EF4444" : "#06B6D4",
                    }}
                  >
                    {a.type === "HIGH_VOLUME" ? "HIGH VOL" : "WHALE"}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span style={{ color: "var(--text-muted)" }}>
                    {(a.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
            {activities.length > 3 && (
              <p className="text-[9px] font-mono text-center pt-1" style={{ color: "var(--text-disabled)" }}>
                +{activities.length - 3} more
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}