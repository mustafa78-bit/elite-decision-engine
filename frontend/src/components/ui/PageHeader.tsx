import React from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-6">
      <div className="space-y-1">
        <h1 className="text-xs font-bold tracking-widest text-[var(--text-primary)] font-mono uppercase">
          {title}
        </h1>
        {subtitle && (
          <p className="text-[10px] text-[var(--text-muted)] font-mono uppercase tracking-[0.05em]">
            {subtitle}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}

interface PageContainerProps {
  children: React.ReactNode;
  className?: string;
}

export function PageContainer({ children, className = "" }: PageContainerProps) {
  return (
    <div className={`space-y-6 max-w-7xl mx-auto px-4 sm:px-6 py-6 ${className}`}>
      {children}
    </div>
  );
}
