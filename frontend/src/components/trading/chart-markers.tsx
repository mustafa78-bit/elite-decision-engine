import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface TradeMarker {
  id: string;
  type: "enter" | "exit" | "tp" | "sl" | "ai";
  symbol: string;
  price: number;
  time: string;
  label: string;
  direction?: "long" | "short";
  confidence?: number;
}

interface ChartMarkersProps {
  markers?: TradeMarker[];
}

const markerConfig = {
  enter: { color: "var(--accent-green)", icon: "▲", badge: "success" as const },
  exit: { color: "var(--accent-red)", icon: "▼", badge: "danger" as const },
  tp: { color: "var(--accent-blue)", icon: "●", badge: "info" as const },
  sl: { color: "var(--accent-yellow)", icon: "◆", badge: "warning" as const },
  ai: { color: "var(--accent-purple)", icon: "✦", badge: "purple" as const },
};

export function ChartMarkers({ markers = [] }: ChartMarkersProps) {
  if (markers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Chart Markers</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No markers on chart
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Markers
          <span className="text-[12px] font-mono text-[var(--text-muted)] ml-2">
            {markers.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {markers.map((m) => {
            const config = markerConfig[m.type];
            return (
              <div
                key={m.id}
                className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
              >
                <div className="flex items-center gap-2">
                  <span style={{ color: config.color }}>{config.icon}</span>
                  <div>
                    <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                      {m.label}
                    </span>
                    <span className="text-[12px] font-mono text-[var(--text-muted)] ml-1">
                      @ {m.price}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5">
                  {m.type === "ai" && m.confidence && (
                    <span className="text-[12px] font-mono text-[var(--text-muted)]">
                      {m.confidence}%
                    </span>
                  )}
                  <Badge variant={config.badge}>
                    {m.type.toUpperCase()}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
