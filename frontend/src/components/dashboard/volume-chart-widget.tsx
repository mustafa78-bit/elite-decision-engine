import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface VolumePoint {
  label: string;
  volume: number;
  isUp: boolean;
}

interface VolumeChartWidgetProps {
  data?: VolumePoint[];
}

export function VolumeChartWidget({ data = [] }: VolumeChartWidgetProps) {
  if (data.length === 0) {
    return (
      <Card className="h-full">
        <CardHeader><CardTitle>Volume</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32 text-sm text-[var(--text-muted)]">
            No volume data
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxVol = Math.max(...data.map((d) => d.volume), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Volume</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-1 h-32">
          {data.map((d, i) => {
            const pct = d.volume / maxVol;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-0.5">
                <div
                  className="w-full rounded-t-sm transition-all"
                  style={{
                    height: `${Math.max(pct * 100, 3)}%`,
                    backgroundColor: d.isUp ? "var(--accent-green)" : "var(--accent-red)",
                    opacity: 0.3 + pct * 0.5,
                  }}
                />
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
