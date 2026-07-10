interface EmptyStateProps {
  message?: string;
  icon?: string;
}

export function EmptyState({
  message = "No data available",
  icon,
}: EmptyStateProps) {
  return (
    <div className="border border-dashed border-[var(--border-subtle)] rounded-lg p-8 text-center flex flex-col items-center gap-2">
      {icon && <span className="text-2xl opacity-30">{icon}</span>}
      <p className="text-xs text-[var(--text-muted)] font-mono uppercase tracking-widest">
        {message}
      </p>
    </div>
  );
}
