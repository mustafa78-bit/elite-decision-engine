import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/toast-provider";
import { fetchPreferences, updateTheme } from "../api/preferences";
import { usePreferencesStore } from "../stores/preferences-store";
import type { UserPreferencesDTO } from "../types/api/preferences";

export default function PreferencesPage() {
  const { t } = useTranslation("preferences");
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
      const data = await fetchPreferences();
      setPrefs(data);
    } catch {
      addGlobalToast(t("toast.loadError"), "error");
    } finally {
      setLoading(false);
    }
  }, [t]);

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
        {t("page.noData")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        {t("page.title")}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>{t("theme.title")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="text-xs text-[var(--text-secondary)] font-mono">
                {t("theme.current")} <span className="text-[var(--text-primary)]">{prefs.theme}</span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const newTheme = prefs.theme === "dark" ? "light" : "dark";
                  try {
                    await updateTheme(newTheme);
                    setPrefs((p) => (p ? { ...p, theme: newTheme } : p));
                    addGlobalToast(t("toast.themeChanged", { theme: newTheme }), "success");
                  } catch {
                    addGlobalToast(t("toast.themeUpdateError"), "error");
                  }
                }}
              >
                {t("actions.toggle")}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("layout.title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">
                {t("layout.sidebar")}{" "}
                <span className="text-[var(--text-primary)]">
                  {sidebarCollapsed ? t("layout.collapsed") : t("layout.expanded")}
                </span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  localToggleSidebar();
                  addGlobalToast(
                    !sidebarCollapsed ? t("toast.sidebarCollapsed") : t("toast.sidebarExpanded"),
                    "success",
                  );
                }}
              >
                {t("actions.toggle")}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("display.title")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-secondary)] font-mono">{t("display.timeFormat")}</span>
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
              <span className="text-xs text-[var(--text-secondary)] font-mono">{t("display.numberFormat")}</span>
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
              <span className="text-xs text-[var(--text-secondary)] font-mono">{t("display.refreshInterval")}</span>
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
              <span className="text-xs text-[var(--text-secondary)] font-mono">{t("display.defaultSymbol")}</span>
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
