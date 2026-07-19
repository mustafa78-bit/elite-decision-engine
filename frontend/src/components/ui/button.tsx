import { forwardRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger" | "glass" | "outline";
  size?: "sm" | "md" | "lg";
  children: ReactNode;
}

const variants: Record<string, string> = {
  primary:
    "bg-[var(--accent-blue)] text-white hover:bg-blue-700 shadow-[0_2px_8px_rgba(37,99,235,0.15)]",
  secondary:
    "bg-white text-[var(--text-primary)] border border-slate-200 hover:bg-slate-50 hover:border-slate-300 shadow-[0_1px_3px_rgba(15,23,42,0.02)]",
  ghost:
    "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-slate-100",
  danger:
    "bg-red-50 text-red-600 hover:bg-red-100 border border-red-200 bg-[var(--accent-red)]/0",
  glass:
    "bg-white/80 backdrop-blur-md text-[var(--text-primary)] hover:bg-slate-50 border border-slate-200/50 shadow-[0_4px_12px_rgba(15,23,42,0.03)]",
  outline:
    "text-[var(--text-secondary)] border border-slate-200 hover:text-[var(--text-primary)] hover:border-slate-300 hover:bg-slate-50",
};

const sizes: Record<string, string> = {
  sm: "h-8 px-3 text-xs rounded-lg",
  md: "h-9 px-4 text-sm rounded-lg",
  lg: "h-11 px-6 text-sm rounded-xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "secondary", size = "md", className, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-all duration-[var(--transition-fast)] cursor-pointer select-none",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-blue)] focus-visible:ring-offset-2 focus-visible:ring-offset-white",
          "disabled:opacity-40 disabled:pointer-events-none",
          variants[variant],
          sizes[size],
          className,
        )}
        {...props}
      >
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
