import { cn } from "../../lib/utils";

interface KbdProps {
  children: string;
  className?: string;
}

export function Kbd({ children, className }: KbdProps) {
  return (
    <kbd
      className={cn(
        "inline-flex items-center justify-center h-5 min-w-[20px] px-1.5 rounded-md",
        "bg-[var(--bg-elevated)] border border-[var(--border-subtle)]",
        "text-[10px] font-mono text-[var(--text-muted)]",
        "shadow-[0_1px_0_var(--border-subtle)]",
        className,
      )}
    >
      {children}
    </kbd>
  );
}
