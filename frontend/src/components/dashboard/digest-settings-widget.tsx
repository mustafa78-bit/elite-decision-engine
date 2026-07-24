import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Switch } from "../ui/switch";

interface DigestSetting {
  id: string;
  label: string;
  enabled: boolean;
  frequency?: string;
}

interface DigestSettingsWidgetProps {
  settings?: DigestSetting[];
  onToggle?: (id: string, enabled: boolean) => void;
}

export function DigestSettingsWidget({
  settings = [],
  onToggle,
}: DigestSettingsWidgetProps) {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Digest Settings</CardTitle>
      </CardHeader>
      <CardContent>
        {settings.length === 0 ? (
          <div className="text-sm text-[var(--text-muted)] text-center py-4">
            No digest settings
          </div>
        ) : (
          <div className="space-y-2">
            {settings.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between py-1.5"
              >
                <div>
                  <div className="text-[13px] font-mono text-[var(--text-secondary)]">
                    {s.label}
                  </div>
                  {s.frequency && (
                    <div className="text-[12px] text-[var(--text-muted)]">
                      {s.frequency}
                    </div>
                  )}
                </div>
                <Switch
                  checked={s.enabled}
                  onCheckedChange={(checked) => onToggle?.(s.id, checked)}
                />
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
