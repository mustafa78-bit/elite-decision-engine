import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface ConcentrationItem {
  label: string;
  value: number;
  color: string;
}

interface ConcentrationWidgetProps {
  items?: ConcentrationItem[];
  herfindahlIndex?: number;
}

export function ConcentrationWidget({
  items = [],
  herfindahlIndex = 0,
}: ConcentrationWidgetProps) {
  const hhiLabel =
    herfindahlIndex < 1000
      ? "Diversified"
      : herfindahlIndex < 2500
        ? "Moderate"
        : "Concentrated";

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Concentration</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">
          HHI: {herfindahlIndex.toFixed(0)} — {hhiLabel}
        </span>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.slice(0, 6).map((item) => (
          <div key={item.label}>
            <div className="flex justify-between text-[10px] mb-0.5">
              <span className="font-mono text-[var(--text-secondary)]">{item.label}</span>
              <span className="font-mono tabular-nums text-[var(--text-primary)]">
                {item.value.toFixed(1)}%
              </span>
            </div>
            <div className="h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${item.value}%`,
                  backgroundColor: item.color,
                }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
