import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

interface Shortcut {
  key: string;
  description: string;
  category: string;
}

const allShortcuts: Shortcut[] = [
  { key: "Ctrl + K", description: "Command palette", category: "Navigation" },
  { key: "/", description: "Global search", category: "Navigation" },
  { key: "Ctrl + B", description: "Toggle sidebar", category: "Navigation" },
  { key: "Esc", description: "Close modal / search", category: "Navigation" },
  { key: "Ctrl + T", description: "New trade", category: "Trading" },
  { key: "Ctrl + R", description: "Refresh data", category: "General" },
  { key: "Ctrl + Shift + F", description: "Global search (alt)", category: "General" },
];

export function KeyboardShortcuts() {
  const [search, setSearch] = useState("");

  const categories = useMemo(() => {
    const filtered = search
      ? allShortcuts.filter(
          (s) =>
            s.description.toLowerCase().includes(search.toLowerCase()) ||
            s.key.toLowerCase().includes(search.toLowerCase()) ||
            s.category.toLowerCase().includes(search.toLowerCase()),
        )
      : allShortcuts;
    return Array.from(new Set(filtered.map((s) => s.category))).map((cat) => ({
      category: cat,
      shortcuts: filtered.filter((s) => s.category === cat),
    }));
  }, [search]);

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Keyboard Shortcuts</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 p-0">
        <div className="px-3 pb-2">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter shortcuts..."
            className="w-full bg-[var(--bg-base)] rounded-lg px-3 py-1.5 text-[12px] font-mono text-[var(--text-primary)] placeholder:text-[var(--text-muted)] border border-[var(--border-subtle)] focus:outline-none focus:border-[var(--accent-blue)]"
          />
        </div>
        {categories.map(({ category, shortcuts }) => (
          <div key={category} className="px-3">
            <div className="text-[12px] font-mono text-[var(--text-muted)] uppercase py-1 border-b border-[var(--border-subtle)]">{category}</div>
            {shortcuts.map((s) => (
              <div key={s.key + s.description} className="flex items-center justify-between py-1 text-[12px] font-mono border-b border-[var(--border-subtle)] last:border-b-0">
                <span className="text-[var(--text-secondary)]">{s.description}</span>
                <kbd className="px-1.5 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[12px] text-[var(--accent-blue)] font-mono">
                  {s.key}
                </kbd>
              </div>
            ))}
          </div>
        ))}
        {categories.length === 0 && (
          <div className="px-3 py-4 text-center text-[12px] text-[var(--text-muted)]">
            No shortcuts match "{search}"
          </div>
        )}
      </CardContent>
    </Card>
  );
}
