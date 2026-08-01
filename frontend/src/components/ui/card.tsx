import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: "default" | "glass" | "elevated";
}

const CARD_VARIANTS: Record<string, string> = {
  default: "widget-card",
  glass: "glass rounded-xl",
  elevated: "surface-elevated rounded-xl",
};

export function Card({
  variant = "default",
  className,
  children,
  ...props
}: CardProps) {

  return (
    <div className={cn(CARD_VARIANTS[variant], className)} {...props}>
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("widget-header", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-xs font-medium text-[var(--text-secondary)] uppercase tracking-[0.08em]",
        className,
      )}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("widget-body", className)} {...props}>
      {children}
    </div>
  );
}
