import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

interface BadgeProps {
  variant?:
    | "default"
    | "success"
    | "warning"
    | "danger"
    | "info"
    | "purple"
    | "cyan";
  children: ReactNode;
  className?: string;
}

const variants: Record<string, string> = {
  default: "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border border-[var(--border-subtle)]",
  success: "bg-green-950/60 text-[var(--accent-green)] border border-green-800/40",
  warning: "bg-yellow-950/60 text-[var(--accent-yellow)] border border-yellow-800/40",
  danger: "bg-red-950/60 text-[var(--accent-red)] border border-red-800/40",
  info: "bg-blue-950/60 text-[var(--accent-blue)] border border-blue-800/40",
  purple: "bg-purple-950/60 text-[var(--accent-purple)] border border-purple-800/40",
  cyan: "bg-cyan-950/60 text-[var(--accent-cyan)] border border-cyan-800/40",
};

export function Badge({
  variant = "default",
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium font-mono rounded-md",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
