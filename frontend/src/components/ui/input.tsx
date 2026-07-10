import { forwardRef } from "react";
import type { InputHTMLAttributes } from "react";
import { cn } from "../../lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={id}
            className="text-[11px] font-medium text-[var(--text-secondary)] uppercase tracking-[0.06em]"
          >
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={id}
          className={cn(
            "h-9 px-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-default)] text-sm text-[var(--text-primary)] font-mono",
            "placeholder:text-[var(--text-muted)]",
            "focus:outline-none focus:border-[var(--accent-blue)] focus:shadow-[0_0_0_1px_var(--accent-blue)]",
            "transition-all duration-[var(--transition-fast)]",
            error && "border-[var(--accent-red)]",
            className,
          )}
          {...props}
        />
        {error && (
          <span className="text-xs text-[var(--accent-red)]">{error}</span>
        )}
      </div>
    );
  },
);

Input.displayName = "Input";
