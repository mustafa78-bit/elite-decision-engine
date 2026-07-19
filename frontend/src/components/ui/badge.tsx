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
  default: "bg-slate-50 text-slate-600 border border-slate-200/60",
  success: "bg-emerald-50 text-emerald-700 border border-emerald-200/50 accent-green",
  warning: "bg-amber-50 text-amber-700 border border-amber-200/50 accent-yellow",
  danger: "bg-rose-50 text-rose-700 border border-rose-200/50 accent-red",
  info: "bg-blue-50 text-blue-700 border border-blue-200/50 accent-blue",
  purple: "bg-purple-50 text-purple-700 border border-purple-200/50 accent-purple",
  cyan: "bg-cyan-50 text-cyan-700 border border-cyan-200/50 accent-cyan",
};

export function Badge({
  variant = "default",
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2.5 py-0.5 text-[10px] font-bold font-mono rounded-md tracking-wider uppercase select-none",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
