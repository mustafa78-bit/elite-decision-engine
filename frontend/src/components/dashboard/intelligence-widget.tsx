import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { formatTime } from "../../lib/utils";

interface IntelligenceItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  relevance?: number;
}

interface IntelligenceWidgetProps {
  items?: IntelligenceItem[];
}

export function IntelligenceWidget({ items = [] }: IntelligenceWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Intelligence</CardTitle>
      </CardHeader>
      <CardContent className="max-h-64 overflow-y-auto">
        {items.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No intelligence data
          </div>
        ) : (
          <div className="space-y-2">
            {items.slice(0, 5).map((item) => (
              <div
                key={item.id}
                className="p-2 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="text-[11px] font-medium text-[var(--text-primary)] leading-tight">
                    {item.title}
                  </div>
                  {item.relevance !== undefined && (
                    <Badge variant="info" className="shrink-0">
                      {item.relevance.toFixed(0)}%
                    </Badge>
                  )}
                </div>
                <div className="text-[10px] text-[var(--text-secondary)] mt-1 line-clamp-2">
                  {item.summary}
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <span className="text-[9px] text-[var(--text-muted)]">
                    {item.source}
                  </span>
                  <span className="text-[9px] font-mono text-[var(--text-muted)]">
                    {formatTime(item.timestamp)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
