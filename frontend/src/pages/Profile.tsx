import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";

export default function Profile() {
  const { t } = useTranslation("profile");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-default)] flex items-center justify-center">
          <span className="text-lg font-mono text-[var(--text-muted)]">U</span>
        </div>
        <div>
          <h1 className="text-sm font-semibold text-[var(--text-primary)]">{t("identity.name")}</h1>
          <p className="text-[10px] font-mono text-[var(--text-muted)]">{t("identity.unavailable")}</p>
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
              <span className="text-xs text-[var(--text-primary)]">{t("identity.unavailable")}</span>
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
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("notificationPreferences.tradeAlerts")}</span>
              <span className="text-xs text-[var(--text-muted)]">{t("identity.unavailable")}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("notificationPreferences.riskWarnings")}</span>
              <span className="text-xs text-[var(--text-muted)]">{t("identity.unavailable")}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-[var(--text-muted)]">{t("notificationPreferences.dailyDigest")}</span>
              <span className="text-xs text-[var(--text-muted)]">{t("identity.unavailable")}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>{t("recentActivity.title")}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <div className="text-[10px] text-[var(--text-muted)] font-mono py-1">
              {t("identity.unavailable")}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
