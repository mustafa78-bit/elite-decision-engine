import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { useAuth } from "../components/auth/AuthProvider";
import { fetchCurrentUser } from "../api/users";
import { fetchPreferences } from "../api/preferences";
import type { LayoutContext } from "../components/layout/Layout";

function formatMemberSince(iso: string | null, locale: string): string | null {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString(locale, { year: "numeric", month: "long", day: "numeric" });
}

export default function Profile() {
  const { t, i18n } = useTranslation("profile");
  const { user } = useAuth();
  const { notifications } = useOutletContext<LayoutContext>();
  const [memberSince, setMemberSince] = useState<string | null>(null);
  const [notificationPrefs, setNotificationPrefs] = useState<Record<string, boolean> | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchCurrentUser()
      .then((u) => { if (mounted) setMemberSince(u.created_at); })
      .catch(() => {});
    fetchPreferences()
      .then((p) => { if (mounted) setNotificationPrefs(p.notification_preferences ?? {}); })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  const recentActivity = [...notifications].reverse().slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
          <span className="text-lg font-mono text-[var(--text-muted)]">
            {user ? user.charAt(0).toUpperCase() : "U"}
          </span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--text-primary)]">{user || t("identity.name")}</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader><CardTitle>{t("account.title")}</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("account.plan")}</span>
              <span className="text-xs text-[var(--text-primary)]">{t("identity.unavailable")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("account.apiCalls24h")}</span>
              <span className="text-xs text-[var(--text-primary)]">{t("identity.unavailable")}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("account.memberSince")}</span>
              <span className="text-xs text-[var(--text-primary)]">
                {formatMemberSince(memberSince, i18n.language) ?? t("identity.unavailable")}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{t("apiKeys.title")}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="p-2 rounded bg-[var(--bg-elevated)] border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[10px] font-mono text-[var(--text-muted)]">{t("identity.unavailable")}</span>
            </div>
            <Button size="sm" variant="secondary" className="w-full text-[10px]" disabled>
              {t("apiKeys.generateNewKey")}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{t("notificationPreferences.title")}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {(["trade_opened", "trade_closed", "system_alert"] as const).map((key) => {
              const labelKey = key === "trade_opened" ? "tradeOpened" : key === "trade_closed" ? "tradeClosed" : "systemAlerts";
              const enabled = notificationPrefs?.[key];
              return (
                <div key={key} className="flex items-center justify-between">
                  <span className="text-xs text-[var(--text-muted)]">{t(`notificationPreferences.${labelKey}`)}</span>
                  <span className={`text-xs ${enabled ? "text-[var(--accent-green)]" : "text-[var(--text-muted)]"}`}>
                    {notificationPrefs === null
                      ? t("identity.unavailable")
                      : enabled
                        ? t("notificationPreferences.on")
                        : t("notificationPreferences.off")}
                  </span>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{t("recentActivity.title")}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {recentActivity.length === 0 ? (
              <div className="text-[10px] text-[var(--text-muted)] font-mono py-1">
                {t("recentActivity.empty")}
              </div>
            ) : (
              recentActivity.map((n, i) => (
                <div key={i} className="flex items-center justify-between text-[10px] font-mono py-1">
                  <span className={n.event === "TRADE_OPENED" ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                    {n.payload.symbol} {n.payload.side} {n.event === "TRADE_OPENED" ? "↑" : "↓"}
                  </span>
                  <span className="text-[var(--text-muted)]">
                    {new Date(n.timestamp).toLocaleTimeString(i18n.language, { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
