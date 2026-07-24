import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface NewsItem {
  id: string;
  title: string;
  source: string;
  sentiment: "positive" | "negative" | "neutral";
  time: string;
  url?: string;
}

interface NewsWidgetProps {
  items?: NewsItem[];
}

export function NewsWidget({ items = [] }: NewsWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>
          Market News
          <span className="text-[12px] font-mono text-[var(--text-muted)] ml-2">
            AI-curated
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <div className="text-xs text-[var(--text-muted)] text-center py-4">
            No news available
          </div>
        ) : (
          <div className="space-y-1.5">
            {items.map((item) => (
              <div
                key={item.id}
                className="px-2 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed">
                    {item.title}
                  </p>
                  <Badge
                    variant={item.sentiment === "positive" ? "success" : item.sentiment === "negative" ? "danger" : "warning"}
                    className="shrink-0"
                  >
                    {item.sentiment}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-1 text-[11px] font-mono text-[var(--text-muted)]">
                  <span>{item.source}</span>
                  <span>{item.time}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
