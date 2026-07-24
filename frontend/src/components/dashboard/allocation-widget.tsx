import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface AllocationItem {
  label: string;
  value: number;
  color: string;
}

interface AllocationWidgetProps {
  allocations?: AllocationItem[];
}

export function AllocationWidget({ allocations = [] }: AllocationWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        {allocations.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No allocation data
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex h-2 rounded-full overflow-hidden">
              {allocations.map((a) => (
                <div
                  key={a.label}
                  className="h-full transition-all"
                  style={{
                    width: `${a.value}%`,
                    backgroundColor: a.color,
                  }}
                />
              ))}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {allocations.map((a) => (
                <div key={a.label} className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-sm shrink-0"
                    style={{ backgroundColor: a.color }}
                  />
                  <span className="text-[12px] font-mono text-[var(--text-secondary)] flex-1">
                    {a.label}
                  </span>
                  <span className="text-[12px] font-mono tabular-nums text-[var(--text-primary)]">
                    {a.value.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
