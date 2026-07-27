interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[var(--border-subtle)] mb-6">
      <div>
        <h1 className="text-sm font-bold tracking-wider text-[var(--text-primary)] uppercase font-mono">
          {title}
        </h1>
        {subtitle && (
          <p className="text-[10px] text-[var(--text-muted)] uppercase tracking-widest mt-1 font-mono">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="flex items-center gap-2 shrink-0">{action}</div>}
    </div>
  );
}
