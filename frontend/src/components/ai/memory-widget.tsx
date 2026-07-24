import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface MemoryEntry {
  id: string;
  type: "trade" | "pattern" | "observation" | "rule";
  content: string;
  timestamp: string;
  relevance: number;
  symbol?: string;
}

interface MemoryWidgetProps {
  entries?: MemoryEntry[];
}

export function MemoryWidget({ entries = [] }: MemoryWidgetProps) {
  if (entries.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>AI Memory</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No memory entries recorded
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          AI Memory
          <span className="text-[12px] font-mono text-[var(--text-muted)] ml-2">
            {entries.length} entries
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          {entries.map((e) => (
            <div
              key={e.id}
              className="px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
            >
              <div className="flex items-center justify-between mb-0.5">
                <div className="flex items-center gap-1.5">
                  <Badge variant={e.type === "trade" ? "success" : e.type === "pattern" ? "info" : e.type === "observation" ? "warning" : "purple"}>
                    {e.type}
                  </Badge>
                  {e.symbol && (
                    <span className="text-[12px] font-mono text-[var(--text-muted)]">
                      {e.symbol}
                    </span>
                  )}
                </div>
                <span className="text-[11px] font-mono text-[var(--text-muted)]">
                  {e.timestamp}
                </span>
              </div>
              <p className="text-[12px] text-[var(--text-secondary)]">
                {e.content}
              </p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
