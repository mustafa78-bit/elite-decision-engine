import { cn } from "../../lib/utils";

interface ProgressProps {
  value: number;
  max?: number;
  className?: string;
  indicatorClassName?: string;
}

export function Progress({ value, max = 100, className, indicatorClassName }: ProgressProps) {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div
      className={cn(
        "h-1.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden",
        className,
      )}
    >
      <div
        className={cn(
          "h-full rounded-full transition-all duration-500",
          indicatorClassName || "bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-purple)]",
        )}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
