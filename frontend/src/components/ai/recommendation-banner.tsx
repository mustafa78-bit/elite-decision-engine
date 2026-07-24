import { motion, AnimatePresence } from "framer-motion";
import { Badge } from "../ui/badge";

interface Recommendation {
  id: string;
  type: "entry" | "exit" | "alert" | "info";
  symbol: string;
  action: string;
  reasoning: string;
  confidence: number;
  priority: "high" | "medium" | "low";
}

interface RecommendationBannerProps {
  recommendation?: Recommendation | null;
  onDismiss?: () => void;
}

const priorityColors: Record<string, { badge: "danger" | "warning" | "info"; dot: string }> = {
  high: { badge: "danger", dot: "var(--accent-red)" },
  medium: { badge: "warning", dot: "var(--accent-yellow)" },
  low: { badge: "info", dot: "var(--accent-blue)" },
};

export function RecommendationBanner({ recommendation, onDismiss }: RecommendationBannerProps) {
  if (!recommendation) return null;

  const colors = priorityColors[recommendation.priority];

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="rounded-xl border border-[var(--border-default)] bg-[var(--bg-elevated)] backdrop-blur-xl p-3 shadow-lg"
      >
        <div className="flex items-start gap-3">
          <span
            className="w-2 h-2 rounded-full mt-1 shrink-0"
            style={{ backgroundColor: colors.dot }}
          />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant={colors.badge}>
                {recommendation.priority.toUpperCase()}
              </Badge>
              <Badge variant="info">{recommendation.type}</Badge>
              <span className="text-[12px] font-mono text-[var(--text-secondary)]">
                {recommendation.symbol} · {recommendation.action}
              </span>
            </div>
            <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed">
              {recommendation.reasoning}
            </p>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-[12px] font-mono text-[var(--text-muted)]">
                AI Confidence: {recommendation.confidence}%
              </span>
            </div>
          </div>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-[var(--text-muted)] hover:text-[var(--text-primary)] text-xs"
            >
              ✕
            </button>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
