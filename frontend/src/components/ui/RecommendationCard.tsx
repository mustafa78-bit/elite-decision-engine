import { Link, useSearchParams } from "react-router-dom";
import { Badge } from "./badge";

export interface Recommendation {
  id: string;
  type: "entry" | "exit" | "alert" | "info" | "rebalance" | "hedge";
  symbol: string;
  action: string;
  reasoning: string;
  confidence: number;
  priority: "high" | "medium" | "low";
}

interface RecommendationCardProps {
  recommendation: Recommendation;
  onDismiss?: () => void;
}

const priorityColors: Record<string, { badge: "danger" | "warning" | "info"; text: string; bg: string }> = {
  high: { badge: "danger", text: "text-[var(--accent-red)]", bg: "bg-[var(--accent-red)]/10" },
  medium: { badge: "warning", text: "text-[var(--accent-yellow)]", bg: "bg-[var(--accent-yellow)]/10" },
  low: { badge: "info", text: "text-[var(--accent-blue)]", bg: "bg-[var(--accent-blue)]/10" },
};

export function RecommendationCard({ recommendation, onDismiss }: RecommendationCardProps) {
  const [searchParams] = useSearchParams();
  const symbolParam = searchParams.get("symbol") || recommendation.symbol || "BTCUSDT";
  const colors = priorityColors[recommendation.priority] || priorityColors.medium;

  return (
    <div className="bg-[var(--bg-elevated)] border border-[var(--border-default)] rounded-xl p-4 shadow-lg hover:border-[var(--border-accent)] transition-all duration-200">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={colors.badge}>
            {recommendation.priority.toUpperCase()}
          </Badge>
          <Badge variant="info">
            {recommendation.type.toUpperCase()}
          </Badge>
          <span className="text-[11px] font-bold text-[var(--text-primary)]">
            {recommendation.symbol}
          </span>
          <span className="text-[11px] text-[var(--text-muted)]">
            · {recommendation.action}
          </span>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs transition-colors"
            aria-label="Dismiss recommendation"
          >
            ✕
          </button>
        )}
      </div>

      <div className="space-y-3">
        <p className="text-[12px] text-[var(--text-primary)] leading-relaxed font-medium">
          {recommendation.reasoning}
        </p>

        <div className="flex items-center justify-between pt-2 border-t border-[var(--border-subtle)]">
          <div className="text-[10px] font-mono text-[var(--text-secondary)]">
            AI Confidence:{" "}
            <span className="font-bold text-[var(--accent-green)]">
              {recommendation.confidence}%
            </span>
          </div>
        </div>

        {/* Dynamic Contextual CTAs */}
        <div className="grid grid-cols-2 gap-2 mt-3 pt-2">
          <Link
            to={`/intelligence?symbol=${symbolParam}`}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--border-default)] hover:border-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/5 text-[11px] font-semibold text-[var(--text-primary)] transition-all"
          >
            ✦ View Evidence
          </Link>
          <Link
            to={`/portfolio?symbol=${symbolParam}`}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--border-default)] hover:border-[var(--accent-purple)] hover:bg-[var(--accent-purple)]/5 text-[11px] font-semibold text-[var(--text-primary)] transition-all"
          >
            ▣ Analyze Portfolio Impact
          </Link>
          <Link
            to={`/risk?symbol=${symbolParam}`}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md border border-[var(--border-default)] hover:border-[var(--accent-red)] hover:bg-[var(--accent-red)]/5 text-[11px] font-semibold text-[var(--text-primary)] transition-all"
          >
            ▲ Open Risk Analysis
          </Link>
          <Link
            to={`/ai-experience?symbol=${symbolParam}`}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md bg-[var(--accent-blue)] hover:bg-[var(--accent-blue)]/90 text-white text-[11px] font-bold shadow-md transition-all"
          >
            ◆ Ask OLLO
          </Link>
        </div>
      </div>
    </div>
  );
}
