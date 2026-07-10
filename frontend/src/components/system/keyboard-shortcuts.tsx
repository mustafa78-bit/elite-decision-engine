import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface Shortcut {
  key: string;
  description: string;
  category: string;
}

export function KeyboardShortcuts() {
  const shortcuts: Shortcut[] = [
    { key: "Ctrl + B", description: "Toggle sidebar", category: "Navigation" },
    { key: "Ctrl + K", description: "Command palette", category: "Navigation" },
    { key: "Ctrl + T", description: "New trade", category: "Trading" },
    { key: "Ctrl + R", description: "Refresh data", category: "General" },
    { key: "Ctrl + P", description: "Position view", category: "Trading" },
    { key: "Ctrl + O", description: "Order book", category: "Trading" },
    { key: "Ctrl + Shift + A", description: "Analytics view", category: "Analytics" },
    { key: "Alt + 1-4", description: "Switch viewport", category: "Layout" },
    { key: "Space", description: "Play/Pause alerts", category: "Alerts" },
    { key: "Esc", description: "Close modal", category: "General" },
    { key: "/", description: "Search", category: "General" },
    { key: "? / Ctrl+/", description: "Toggle shortcuts help", category: "Help" },
  ];

  const categories = Array.from(new Set(shortcuts.map((s) => s.category)));

  return (
    <Card className="h-full">
      <CardHeader><CardTitle>Keyboard Shortcuts</CardTitle></CardHeader>
      <CardContent className="space-y-2 p-0">
        {categories.map((cat) => (
          <div key={cat} className="px-3">
            <div className="text-[9px] font-mono text-[var(--text-muted)] uppercase py-1 border-b border-[var(--border-subtle)]">{cat}</div>
            {shortcuts
              .filter((s) => s.category === cat)
              .map((s) => (
                <div key={s.key} className="flex items-center justify-between py-1 text-[10px] font-mono border-b border-[var(--border-subtle)] last:border-b-0">
                  <span className="text-[var(--text-secondary)]">{s.description}</span>
                  <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[9px] text-[var(--accent-blue)] font-mono">
                    {s.key}
                  </kbd>
                </div>
              ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
