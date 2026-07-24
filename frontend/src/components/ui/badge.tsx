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
  success: "bg-[var(--bg-elevated)] text-[var(--accent-green)] border border-[var(--accent-green)]/30",
  warning: "bg-[var(--bg-elevated)] text-[var(--accent-yellow)] border border-[var(--accent-yellow)]/30",
  danger: "bg-[var(--bg-elevated)] text-[var(--accent-red)] border border-[var(--accent-red)]/30",
  info: "bg-[var(--bg-elevated)] text-[var(--accent-blue)] border border-[var(--accent-blue)]/30",
  purple: "bg-[var(--bg-elevated)] text-[var(--accent-purple)] border border-[var(--accent-purple)]/30",
  cyan: "bg-[var(--bg-elevated)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30",
};

export function Badge({
  variant = "default",
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 text-[13px] font-medium font-mono rounded-md",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
