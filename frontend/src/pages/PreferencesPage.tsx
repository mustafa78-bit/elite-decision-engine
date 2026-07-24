import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/toast-provider";
import { fetchPreferences, updateTheme } from "../api/preferences";
import { usePreferencesStore } from "../stores/preferences-store";
import type { UserPreferencesDTO } from "../types/api/preferences";

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<UserPreferencesDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const localPrefs = usePreferencesStore();
  const {
    refreshInterval,
    setRefreshInterval,
    timeFormat,
    setTimeFormat,
    numberFormat,
    setNumberFormat,
    defaultSymbol,
    setDefaultSymbol,
    sidebarCollapsed,
    toggleSidebar: localToggleSidebar,
  } = localPrefs;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPreferences(1);
      setPrefs(data);
    } catch {
      addGlobalToast("Failed to load preferences", "error");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  if (!prefs) {
    return (
      <div className="text-xs text-[var(--text-secondary)] font-mono uppercase">
        No preferences data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        Founder Settings
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="text-xs text-[var(--text-secondary)] font-mono">
                Current: <span className="text-[var(--text-primary)]">{prefs.theme}</span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const newTheme = prefs.theme === "dark" ? "light" : "dark";
                  try {
                    await updateTheme(1, newTheme);
                    setPrefs((p) => (p ? { ...p, theme: newTheme } : p));
                    addGlobalToast(`Theme changed to ${newTheme}`, "success");
                  } catch {
                    addGlobalToast("Failed to update theme", "error");
                  }
                }}
              >
                Toggle
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Layout</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">
                Sidebar:{" "}
                <span className="text-[var(--text-primary)]">
                  {sidebarCollapsed ? "Collapsed" : "Expanded"}
                </span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  localToggleSidebar();
                  addGlobalToast(
                    `Sidebar ${!sidebarCollapsed ? "collapsed" : "expanded"}`,
                    "success",
                  );
                }}
              >
                Toggle
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Display</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">Time Format</span>
              <div className="flex gap-1">
                {(["12h", "24h"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setTimeFormat(f)}
                    className={`px-2 py-0.5 rounded text-[12px] font-mono border ${
                      timeFormat === f
                        ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                        : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">Number Format</span>
              <div className="flex gap-1">
                {(["usd", "compact"] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => setNumberFormat(f)}
                    className={`px-2 py-0.5 rounded text-[12px] font-mono border capitalize ${
                      numberFormat === f
                        ? "bg-[var(--accent-blue)]/20 border-[var(--accent-blue)] text-[var(--accent-blue)]"
                        : "bg-[var(--bg-base)] border-[var(--border-subtle)] text-[var(--text-muted)]"
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">Refresh Interval</span>
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2 py-0.5 text-[12px] font-mono text-[var(--text-primary)]"
              >
                <option value={5000}>5s</option>
                <option value={10000}>10s</option>
                <option value={30000}>30s</option>
                <option value={60000}>1m</option>
                <option value={300000}>5m</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">Default Symbol</span>
              <input
                type="text"
                value={defaultSymbol}
                onChange={(e) => setDefaultSymbol(e.target.value.toUpperCase())}
                className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2 py-0.5 text-[12px] font-mono text-[var(--text-primary)] w-28 text-right"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
