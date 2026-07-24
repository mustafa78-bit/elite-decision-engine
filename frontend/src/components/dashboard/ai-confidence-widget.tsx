import { motion } from "framer-motion";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

interface AIConfidenceWidgetProps {
  confidence?: number;
  decision?: string;
  score?: number;
}

export function AIConfidenceWidget({
  confidence = 0,
  decision = "WAIT",
  score = 0,
}: AIConfidenceWidgetProps) {
  const pct = Math.min(Math.max((confidence || score) * 10, 0), 100);
  const color =
    pct >= 70
      ? "var(--accent-green)"
      : pct >= 40
        ? "var(--accent-yellow)"
        : "var(--accent-red)";

  return (
    <Card className="h-full">
      <CardContent className="p-4">
        <div className="text-[12px] font-medium text-[var(--text-muted)] uppercase tracking-[0.08em] mb-3">
          AI Confidence
        </div>
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
              <circle
                cx="32"
                cy="32"
                r="28"
                fill="none"
                stroke="var(--bg-elevated)"
                strokeWidth="4"
              />
              <motion.circle
                cx="32"
                cy="32"
                r="28"
                fill="none"
                stroke={color}
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={`${(pct / 100) * 176} 176`}
                initial={{ strokeDasharray: "0 176" }}
                animate={{ strokeDasharray: `${(pct / 100) * 176} 176` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-mono font-bold tabular-nums" style={{ color }}>
                {pct.toFixed(0)}%
              </span>
            </div>
          </div>
          <div className="space-y-1.5">
            <Badge
              variant={
                decision === "BUY" || decision === "STRONG_BUY"
                  ? "success"
                  : decision === "SELL" || decision === "STRONG_SELL"
                    ? "danger"
                    : "warning"
              }
            >
              {decision}
            </Badge>
            <div className="text-[13px] font-mono text-[var(--text-muted)]">
              Score: {score.toFixed(1)}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
