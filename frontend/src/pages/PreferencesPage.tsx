import { useCallback, useEffect, useState } from "react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Skeleton } from "../components/ui/skeleton";
import { addGlobalToast } from "../components/layout/ToastProvider";
import { fetchPreferences, updateTheme, updateLayout } from "../api/preferences";
import type { UserPreferencesDTO } from "../types/api/preferences";

export default function PreferencesPage() {
  const [prefs, setPrefs] = useState<UserPreferencesDTO | null>(null);
  const [loading, setLoading] = useState(true);

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
      <div className="text-xs text-gray-500 font-mono uppercase">
        No preferences data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xs uppercase tracking-widest text-gray-500">
        User Preferences
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Theme</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400 font-mono">
                Current: <span className="text-gray-200">{prefs.theme}</span>
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
          <CardContent>
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400 font-mono">
                Sidebar:{" "}
                <span className="text-gray-200">
                  {prefs.layout_config?.sidebar_collapsed ? "Collapsed" : "Expanded"}
                </span>
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  const collapsed = !prefs.layout_config?.sidebar_collapsed;
                  try {
                    await updateLayout(1, { sidebar_collapsed: collapsed });
                    setPrefs((p) =>
                      p
                        ? {
                            ...p,
                            layout_config: { ...p.layout_config, sidebar_collapsed: collapsed },
                          }
                        : p,
                    );
                    addGlobalToast(
                      `Sidebar ${collapsed ? "collapsed" : "expanded"}`,
                      "success",
                    );
                  } catch {
                    addGlobalToast("Failed to update layout", "error");
                  }
                }}
              >
                Toggle
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
