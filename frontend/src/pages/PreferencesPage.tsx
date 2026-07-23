import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/toast-provider";
import { fetchPreferences } from "../api/preferences";
import { usePreferencesStore } from "../stores/preferences-store";
import type { UserPreferencesDTO } from "../types/api/preferences";
import { useTheme, type ThemeType, type AccentType, type DensityType } from "../components/theme/ThemeProvider";

const ACCENTS: { name: string; value: AccentType; color: string }[] = [
  { name: "Cyber Blue", value: "blue", color: "#4F8CFF" },
  { name: "Electric Violet", value: "violet", color: "#8B5CF6" },
  { name: "Jade Green", value: "green", color: "#10B981" },
  { name: "Amber Orange", value: "orange", color: "#F59E0B" },
  { name: "Rose Red", value: "red", color: "#F43F5E" },
];

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<UserPreferencesDTO | null>(null);
  const [loading, setLoading] = useState(true);

  const {
    theme,
    setTheme,
    accent,
    setAccent,
    density,
    setDensity,
    autoTheme,
    setAutoTheme,
  } = useTheme();

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
        {/* Advanced Appearance & Personalization Options */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle>Appearance & Personalization</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">

            {/* Theme Selection */}
            <div className="space-y-2">
              <label className="text-xs text-[var(--text-secondary)] font-mono block">THEME ENVIRONMENT</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { name: "Terminal Dark", value: "terminal-dark" as ThemeType, desc: "Original high-contrast dashboard" },
                  { name: "Midnight Pro", value: "midnight-pro" as ThemeType, desc: "Luxurious deep violet cyberdeck" },
                  { name: "Professional Light", value: "professional-light" as ThemeType, desc: "Clean, high-readability mode" },
                ].map((t) => (
                  <button
                    key={t.value}
                    disabled={autoTheme}
                    onClick={() => {
                      setTheme(t.value);
                      addGlobalToast(`Theme switched to ${t.name}`, "success");
                    }}
                    className={`flex flex-col items-start p-3 rounded-lg border text-left transition-all ${
                      theme === t.value && !autoTheme
                        ? "bg-[var(--bg-glass)] border-[var(--accent-blue)] ring-1 ring-[var(--accent-blue)]"
                        : "bg-[var(--bg-elevated)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
                    } ${autoTheme ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}
                  >
                    <span className="text-xs font-semibold text-[var(--text-primary)]">{t.name}</span>
                    <span className="text-[10px] text-[var(--text-muted)] mt-1 leading-normal">{t.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Accent Color Customizer */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 py-3 border-t border-b border-[var(--border-subtle)]">
              <div className="space-y-1">
                <label className="text-xs text-[var(--text-secondary)] font-mono block">ACCENT COLOR WAY</label>
                <p className="text-[10px] text-[var(--text-muted)] leading-relaxed">Customize buttons, active indicators, and critical badges</p>
              </div>
              <div className="flex items-center gap-2.5">
                {ACCENTS.map((item) => (
                  <button
                    key={item.value}
                    onClick={() => {
                      setAccent(item.value);
                      addGlobalToast(`Accent color Way changed to ${item.name}`, "success");
                    }}
                    title={item.name}
                    className={`w-6 h-6 rounded-full flex items-center justify-center transition-all ${
                      accent === item.value ? "ring-2 ring-offset-2 ring-offset-[var(--bg-deep)] ring-[var(--accent-blue)]" : "opacity-80 hover:opacity-100"
                    }`}
                    style={{ backgroundColor: item.color }}
                  >
                    {accent === item.value && (
                      <span className="w-1.5 h-1.5 bg-white rounded-full" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* UI Density Selection */}
            <div className="space-y-2">
              <label className="text-xs text-[var(--text-secondary)] font-mono block">UI SPACING DENSITY</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { name: "Compact", value: "compact" as DensityType, desc: "Maximum terminal data compression" },
                  { name: "Comfortable", value: "comfortable" as DensityType, desc: "Balanced professional layout" },
                  { name: "Spacious", value: "spacious" as DensityType, desc: "Large targets and generous whitespace" },
                ].map((d) => (
                  <button
                    key={d.value}
                    onClick={() => {
                      setDensity(d.value);
                      addGlobalToast(`Density configured to ${d.name}`, "success");
                    }}
                    className={`flex flex-col items-start p-3 rounded-lg border text-left transition-all ${
                      density === d.value
                        ? "bg-[var(--bg-glass)] border-[var(--accent-blue)] ring-1 ring-[var(--accent-blue)]"
                        : "bg-[var(--bg-elevated)] border-[var(--border-subtle)] hover:border-[var(--border-default)]"
                    }`}
                  >
                    <span className="text-xs font-semibold text-[var(--text-primary)]">{d.name}</span>
                    <span className="text-[10px] text-[var(--text-muted)] mt-1 leading-normal">{d.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Optional Automatic Theme Switcher */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">
              <div className="space-y-1">
                <span className="text-xs font-semibold text-[var(--text-primary)]">Automatic Theme Switching</span>
                <p className="text-[10px] text-[var(--text-muted)] leading-relaxed">Match system environment preference (Light in daytime, Terminal Dark at night)</p>
              </div>
              <Button
                size="sm"
                variant={autoTheme ? "primary" : "outline"}
                onClick={() => {
                  const next = !autoTheme;
                  setAutoTheme(next);
                  addGlobalToast(
                    `Automatic theme switching ${next ? "enabled" : "disabled"}`,
                    "success"
                  );
                }}
              >
                {autoTheme ? "Enabled" : "Disabled"}
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
                    className={`px-2 py-0.5 rounded text-[10px] font-mono border ${
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
                    className={`px-2 py-0.5 rounded text-[10px] font-mono border capitalize ${
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
                className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2 py-0.5 text-[10px] font-mono text-[var(--text-primary)]"
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
                className="bg-[var(--bg-base)] border border-[var(--border-subtle)] rounded px-2 py-0.5 text-[10px] font-mono text-[var(--text-primary)] w-28 text-right"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
