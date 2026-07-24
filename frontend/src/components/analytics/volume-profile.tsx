import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface VolumeLevel {
  price: number;
  volume: number;
  poc: boolean;
}

interface VolumeProfileProps {
  symbol?: string;
  levels?: VolumeLevel[];
}

export function VolumeProfile({
  symbol = "BTC/USDT",
  levels = [
    { price: 43300, volume: 1200, poc: false },
    { price: 43200, volume: 2100, poc: false },
    { price: 43100, volume: 3400, poc: false },
    { price: 43000, volume: 5200, poc: true },
    { price: 42900, volume: 4800, poc: false },
    { price: 42800, volume: 3900, poc: false },
    { price: 42700, volume: 2500, poc: false },
    { price: 42600, volume: 1500, poc: false },
    { price: 42500, volume: 800, poc: false },
  ],
}: VolumeProfileProps) {
  const maxVol = Math.max(...levels.map((l) => l.volume), 1);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Volume Profile</CardTitle>
        <span className="text-[12px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="p-2 space-y-0.5">
        {levels.sort((a, b) => b.price - a.price).map((l) => (
          <div key={l.price} className="flex items-center gap-2 h-5">
            <span className="w-14 text-[12px] font-mono text-[var(--text-muted)] text-right tabular-nums">${(l.price / 1000).toFixed(1)}K</span>
            <div className="flex-1 h-full rounded-sm bg-[var(--bg-base)] overflow-hidden relative">
              <div
                className={`h-full rounded-sm ${l.poc ? "bg-[var(--accent-blue)]/40" : "bg-[var(--accent-blue)]/15"}`}
                style={{ width: `${(l.volume / maxVol) * 100}%` }}
              />
              {l.poc && (
                <span className="absolute right-1 top-0 text-[11px] font-mono text-[var(--accent-blue)] leading-5">POC</span>
              )}
            </div>
            <span className="w-10 text-[11px] font-mono text-[var(--text-muted)] tabular-nums">{(l.volume / 1000).toFixed(1)}K</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
