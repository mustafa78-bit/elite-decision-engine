import React from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 mb-5 border-b border-[var(--border-subtle)] gap-4">
      <div className="space-y-1">
        <h1 className="text-xs font-bold uppercase tracking-[0.2em] text-[var(--text-primary)]">
          {title}
        </h1>
        {subtitle && (
          <p className="text-[11px] text-[var(--text-muted)] font-mono font-medium tracking-wide">
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0 self-start sm:self-center">
          {actions}
        </div>
      )}
    </div>
  );
}
