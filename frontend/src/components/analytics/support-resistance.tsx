import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";

interface SRLevel {
  price: number;
  type: "support" | "resistance";
  strength: "strong" | "moderate" | "weak";
  touches: number;
}

interface SupportResistanceProps {
  symbol?: string;
  levels?: SRLevel[];
}

export function SupportResistance({
  symbol = "BTC/USDT",
  levels = [
    { price: 41500, type: "support", strength: "strong", touches: 5 },
    { price: 42000, type: "support", strength: "moderate", touches: 3 },
    { price: 42500, type: "support", strength: "weak", touches: 1 },
    { price: 43200, type: "resistance", strength: "strong", touches: 4 },
    { price: 43800, type: "resistance", strength: "moderate", touches: 2 },
    { price: 44500, type: "resistance", strength: "weak", touches: 1 },
  ],
}: SupportResistanceProps) {
  const strengthColor = { strong: "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)]/30", moderate: "bg-[var(--bg-elevated)] border-[var(--border-default)]", weak: "bg-[var(--bg-base)] border-[var(--border-subtle)]" };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>S/R Levels</CardTitle>
        <span className="text-[10px] font-mono text-[var(--text-muted)]">{symbol}</span>
      </CardHeader>
      <CardContent className="space-y-1">
        {levels.sort((a, b) => b.price - a.price).map((l) => (
          <div
            key={`${l.type}-${l.price}`}
            className={`flex items-center justify-between px-2 py-1.5 rounded-lg text-[10px] font-mono border ${strengthColor[l.strength]}`}
          >
            <div className="flex items-center gap-1.5">
              <span className={`w-1 h-4 rounded-full ${l.type === "support" ? "bg-[var(--accent-green)]" : "bg-[var(--accent-red)]"}`} />
              <span className="text-[var(--text-primary)] tabular-nums">${l.price.toLocaleString()}</span>
              <Badge variant={l.type === "support" ? "success" : "danger"} className="text-[8px]">{l.type}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-[9px] ${l.strength === "strong" ? "text-[var(--accent-blue)]" : "text-[var(--text-muted)]"}`}>{l.strength}</span>
              <span className="text-[9px] text-[var(--text-muted)]">{l.touches}t</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
