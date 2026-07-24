import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface CorrelationPair {
  a: string;
  b: string;
  value: number;
}

interface CorrelationMatrixProps {
  pairs?: CorrelationPair[];
}

export function CorrelationMatrix({
  pairs = [
    { a: "BTC", b: "ETH", value: 0.82 },
    { a: "BTC", b: "SOL", value: 0.65 },
    { a: "BTC", b: "AVAX", value: 0.58 },
    { a: "BTC", b: "LINK", value: 0.45 },
    { a: "ETH", b: "SOL", value: 0.71 },
    { a: "ETH", b: "AVAX", value: 0.62 },
    { a: "ETH", b: "LINK", value: 0.50 },
    { a: "SOL", b: "AVAX", value: 0.78 },
    { a: "SOL", b: "LINK", value: 0.55 },
    { a: "AVAX", b: "LINK", value: 0.60 },
  ],
}: CorrelationMatrixProps) {
  const assets = Array.from(new Set(pairs.flatMap((p) => [p.a, p.b])));

  const getColor = (v: number) => {
    if (v > 0.7) return "bg-[var(--accent-green)]/30 text-[var(--accent-green)]";
    if (v > 0.4) return "bg-yellow-500/20 text-yellow-400";
    if (v > 0.2) return "bg-orange-500/20 text-orange-400";
    return "bg-[var(--accent-red)]/30 text-[var(--accent-red)]";
  };

  const getCorrelation = (a: string, b: string) => {
    if (a === b) return null;
    return pairs.find((p) => (p.a === a && p.b === b) || (p.a === b && p.b === a));
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Correlation Matrix</CardTitle>
      </CardHeader>
      <CardContent className="p-2">
        <div className="grid gap-0.5" style={{ gridTemplateColumns: `60px repeat(${assets.length}, 1fr)` }}>
          <div />
          {assets.map((a) => (
            <div key={a} className="text-[11px] font-mono text-[var(--text-muted)] text-center py-1">{a}</div>
          ))}
          {assets.map((a) => (
            <>
              <div key={`label-${a}`} className="text-[11px] font-mono text-[var(--text-muted)] flex items-center">{a}</div>
              {assets.map((b) => {
                const corr = getCorrelation(a, b);
                return (
                  <div
                    key={`${a}-${b}`}
                    className={`text-[12px] font-mono tabular-nums text-center py-1.5 rounded ${corr ? getColor(corr.value) : "bg-[var(--bg-base)]"}`}
                  >
                    {corr ? corr.value.toFixed(2) : "—"}
                  </div>
                );
              })}
            </>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
