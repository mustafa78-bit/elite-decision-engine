import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface PriorityItem {
  id: string;
  title: string;
  priority: "HIGH" | "MEDIUM" | "LOW";
  timestamp: string;
}

interface PriorityInboxWidgetProps {
  items?: PriorityItem[];
}

export function PriorityInboxWidget({ items = [] }: PriorityInboxWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Priority Inbox</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          {items.filter((i) => i.priority === "HIGH").length} high
        </span>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            Inbox empty
          </div>
        ) : (
          <div className="space-y-1">
            {items.slice(0, 6).map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between py-1.5 border-b border-[var(--border-subtle)] last:border-0"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      item.priority === "HIGH"
                        ? "bg-[var(--accent-red)]"
                        : item.priority === "MEDIUM"
                          ? "bg-[var(--accent-yellow)]"
                          : "bg-[var(--accent-green)]"
                    }`}
                  />
                  <span className="text-[10px] text-[var(--text-secondary)]">
                    {item.title}
                  </span>
                </div>
                <Badge
                  variant={
                    item.priority === "HIGH"
                      ? "danger"
                      : item.priority === "MEDIUM"
                        ? "warning"
                        : "success"
                  }
                >
                  {item.priority}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
