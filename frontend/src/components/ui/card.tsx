import type { HTMLAttributes, ReactNode } from "react";
import { cn } from "../../lib/utils";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  variant?: "default" | "glass" | "elevated";
}

const CARD_VARIANTS: Record<string, string> = {
  default: "bg-white border border-slate-200/80 rounded-2xl shadow-[0_2px_8px_rgba(15,23,42,0.02)] hover:border-slate-300 transition-all duration-300",
  glass: "bg-white/80 backdrop-blur-md border border-slate-200/50 rounded-2xl shadow-[0_4px_16px_rgba(15,23,42,0.03)]",
  elevated: "bg-white border border-slate-200 rounded-2xl shadow-[0_12px_24px_rgba(15,23,42,0.04)]",
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
    <div className={cn("px-6 pt-5 pb-0 flex items-center justify-between", className)} {...props}>
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
        "text-xs font-bold text-slate-900 uppercase tracking-wider",
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
    <div className={cn("px-6 py-5", className)} {...props}>
      {children}
    </div>
  );
}
