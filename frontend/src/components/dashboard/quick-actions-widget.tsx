import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface Action {
  label: string;
  icon: string;
  shortcut?: string;
  onClick?: () => void;
}

interface QuickActionsWidgetProps {
  actions?: Action[];
}

export function QuickActionsWidget({ actions = [] }: QuickActionsWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2">
          {actions.map((action) => (
            <button
              key={action.label}
              onClick={action.onClick}
              className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[11px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-default)] hover:bg-[var(--bg-elevated)]/80 transition-all text-left"
            >
              <span className="text-base">{action.icon}</span>
              <span className="flex-1">{action.label}</span>
              {action.shortcut && (
                <span className="text-[9px] font-mono text-[var(--text-muted)] px-1 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  {action.shortcut}
                </span>
              )}
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
