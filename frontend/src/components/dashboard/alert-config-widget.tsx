import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Switch } from "../ui/switch";

interface AlertRule {
  id: string;
  name: string;
  enabled: boolean;
  type: string;
}

interface AlertConfigWidgetProps {
  rules?: AlertRule[];
  onToggle?: (id: string, enabled: boolean) => void;
}

export function AlertConfigWidget({
  rules = [],
  onToggle,
}: AlertConfigWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Alert Rules</CardTitle>
        <span className="text-[12px] font-mono text-[var(--text-muted)]">
          {rules.filter((r) => r.enabled).length} active
        </span>
      </CardHeader>
      <CardContent>
        {rules.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No alert rules configured
          </div>
        ) : (
          <div className="space-y-1">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="flex items-center justify-between py-2 border-b border-[var(--border-subtle)] last:border-0"
              >
                <div>
                  <div className="text-[13px] font-mono text-[var(--text-secondary)]">
                    {rule.name}
                  </div>
                  <div className="text-[12px] text-[var(--text-muted)]">{rule.type}</div>
                </div>
                <Switch
                  checked={rule.enabled}
                  onCheckedChange={(checked) => onToggle?.(rule.id, checked)}
                />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
