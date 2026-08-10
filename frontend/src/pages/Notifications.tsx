import { useTranslation } from "react-i18next";
import NotificationCenter from "../components/notifications/NotificationCenter";

export default function Notifications() {
  const { t } = useTranslation("notifications");

  return (
    <div className="space-y-4">
      <h2 className="text-xs uppercase tracking-widest text-[var(--text-secondary)]">
        {t("page.title")}
      </h2>
      <NotificationCenter />
    </div>
  );
}
