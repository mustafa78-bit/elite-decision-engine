import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "../ui/card";
import { Badge } from "../ui/badge";

interface DecisionTraceEvent {
  time: string;
  step: string;
  status: "OK" | "WARN" | "INFO";
}

const defaultTrace: DecisionTraceEvent[] = [
  { time: "0s", step: "Market scan triggered", status: "INFO" },
  { time: "+0.1s", step: "Sentiment weight checking", status: "OK" },
  { time: "+0.3s", step: "Multi-timeframe technical align", status: "OK" },
  { time: "+0.4s", step: "Risk exposure guard validation", status: "OK" },
  { time: "+0.5s", step: "Decision execution authorized", status: "OK" },
];

interface AIDecisionCenterWidgetProps {
  decision?: string;
  confidence?: number;
  score?: number;
}

export function AIDecisionCenterWidget({
  decision = "STRONG_BUY",
  confidence = 0.88,
  score = 8.5,
}: AIDecisionCenterWidgetProps) {
  const navigate = useNavigate();
  const pct = confidence * 100;
  const isBuy = decision.includes("BUY");
  const isSell = decision.includes("SELL");

  return (
    <Card
      className="h-full border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--border-default)] transition-all flex flex-col justify-between"
      role="region"
      aria-label="AI Decision Center"
    >
      <CardContent className="p-2.5 flex flex-col h-full justify-between gap-1.5">
        <div>
          <div className="flex items-center justify-between mb-1.5 pb-1 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">AI Decision Center</span>
            <span className="text-[9px] text-[var(--text-muted)] font-mono">◈ Live</span>
          </div>

          <div className="flex items-center justify-between gap-2 mb-2">
            <div>
              <div className="text-[8px] text-[var(--text-muted)] uppercase tracking-wider font-mono">Model Verdict</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Badge variant={isBuy ? "success" : isSell ? "danger" : "warning"} className="text-[10px] font-bold font-mono px-1.5 py-0">
                  {decision}
                </Badge>
                <span className="text-[11px] font-mono font-bold text-[var(--text-primary)]">{pct.toFixed(0)}% Conf</span>
              </div>
            </div>
            <button
              onClick={() => navigate("/decisions")}
              className="px-2 py-1 rounded bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/80 text-[var(--text-inverse)] font-bold text-[10px] transition-colors"
            >
              Explain &rarr;
            </button>
          </div>

          {/* Decision Trace Timeline */}
          <div className="space-y-1">
            <div className="text-[8px] text-[var(--text-muted)] uppercase font-mono tracking-wider">Decision Trace Timeline</div>
            <div className="space-y-1 font-mono text-[9px] max-h-[110px] overflow-y-auto">
              {defaultTrace.map((dt, idx) => (
                <div key={idx} className="flex items-center justify-between hover:bg-[var(--bg-hover)] px-1 py-0.5 rounded transition-colors">
                  <div className="flex items-center gap-1">
                    <span className="text-[var(--text-muted)] w-8">{dt.time}</span>
                    <span className="text-[var(--text-secondary)] truncate max-w-[170px]">{dt.step}</span>
                  </div>
                  <span className={dt.status === "OK" ? "text-[var(--accent-green)] font-semibold" : "text-[var(--accent-cyan)]"}>
                    {dt.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-1.5 pt-1 border-t border-[var(--border-subtle)] flex items-center justify-between text-[9px] font-mono text-[var(--text-muted)]">
          <span>Target Symbol: BTC/USDT</span>
          <span>Score: {score.toFixed(1)}/10</span>
        </div>
      </CardContent>
    </Card>
  );
}
